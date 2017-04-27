!=============================================================================
! Modified version of AMR2CELL.f90 from the RAMSES source
!=============================================================================
subroutine ramses_data(infile,nmax,nvarmax,lmax2,var_read,xcenter,ycenter,zcenter,deltax,deltay,deltaz,&
                     & lscale,ud,ul,ut,quiet,data_array,ncells,failed)
        
  implicit none
  
  ! Subroutine arguments
  character(LEN=*)              , intent(in ) :: infile,var_read
  integer                       , intent(in ) :: nmax,nvarmax,lmax2
  real*8                        , intent(in ) :: xcenter,ycenter,zcenter,deltax,deltay,deltaz,lscale
  real*8                        , intent(in ) :: ud,ul,ut
  logical                       , intent(in ) :: quiet
  
  integer                       , intent(out) :: ncells
  real*8,dimension(nmax,nvarmax), intent(out) :: data_array
  logical                       , intent(out) :: failed
  
  ! Variables
  integer :: ncpu,ndim
  integer :: i,j,k,l,twotondim,ivar,jvar,nboundary,ngrid_current
  integer :: nx,ny,nz,ilevel,n,icell,ngrp,nlevelmax,lmax,ind,ipos,ngrida
  integer :: ngridmax,icpu,ncpu_read,nvarh
  integer :: ix,iy,iz,istep,iprog,percentage
  integer, dimension(:  ), allocatable :: cpu_list
  integer, dimension(:,:), allocatable :: son,ngridfile,ngridlevel,ngridbound
  
  real*8 :: xmin,xmax,ymin,ymax,zmin,zmax,boxlen,dx,dx2
  real*8, dimension(:,:    ), allocatable :: x,xg
  real*8, dimension(:,:,:  ), allocatable :: var
  real*8, dimension(1:8,1:3)              :: xc
  real*8, dimension(    1:3)              :: xbound
  
  character(LEN=5  ) :: nchar,ncharcpu
  character(LEN=50 ) :: string
  character(LEN=128) :: nomfich,repository
  
  logical                            :: ok,ok_cell
  logical, dimension(:), allocatable :: ref,ok_read
  
  !=============================================================================
  
  failed = .false.
  lmax = lmax2
  repository = trim(infile)
  xmin=0.0d0
  xmax=1.0d0
  ymin=0.0d0
  ymax=1.0d0
  zmin=0.0d0
  zmax=1.0d0
  xbound=(/0.0d0,0.0d0,0.0d0/)

  !-----------------------------------------------
  ! Reading RAMSES data
  !-----------------------------------------------
  ipos=INDEX(repository,'output_')
  nchar=repository(ipos+7:ipos+13)
  nomfich=TRIM(repository)//'/hydro_'//TRIM(nchar)//'.out00001'
  inquire(file=nomfich, exist=ok) ! verify input file 
  if ( .not. ok ) then
     if(.not. quiet) write(*,'(a)') TRIM(nomfich)//' not found.'
     failed = .true.
     return
  endif
  nomfich=TRIM(repository)//'/amr_'//TRIM(nchar)//'.out00001'
  inquire(file=nomfich, exist=ok) ! verify input file 
  if ( .not. ok ) then
     if(.not. quiet) write(*,'(a)') TRIM(nomfich)//' not found.'
     failed = .true.
     return
  endif

  nomfich=TRIM(repository)//'/amr_'//TRIM(nchar)//'.out00001'
  open(unit=10,file=nomfich,status='old',form='unformatted')
  read (10) ncpu
  read (10) ndim
  read (10) nx,ny,nz
  read (10) nlevelmax
  read (10) ngridmax
  read (10) nboundary
  read (10) ngrid_current
  read (10) boxlen
  close(10)
  twotondim=2**ndim
  xbound=(/dble(nx/2),dble(ny/2),dble(nz/2)/)
  
  allocate(ngridfile(1:ncpu+nboundary,1:nlevelmax))
  allocate(ngridlevel(1:ncpu,1:nlevelmax))
  if(nboundary>0)allocate(ngridbound(1:nboundary,1:nlevelmax))
  
  ! Open HYDRO file and read number of variables
  nomfich=TRIM(repository)//'/hydro_'//TRIM(nchar)//'.out00001'
  open(unit=11,file=nomfich,status='old',form='unformatted')
  read (11)
  read (11) nvarh
  close(11)
     
  ! Set which variables are to be read
  allocate(ok_read(1:nvarh+5))
  do i = 1,nvarh+5
     l = 2*(i-1) + 1
     read(var_read(l:l),'(i1)') j
     ok_read(i) = (j == 1)
  enddo
    
  allocate(cpu_list(1:ncpu))
  
  if(deltax > 0.0d0)then
     xmin = xcenter - 0.5d0*deltax*lscale/(boxlen*ul)
     xmax = xcenter + 0.5d0*deltax*lscale/(boxlen*ul)
  endif
  if(deltay > 0.0d0)then
     ymin = ycenter - 0.5d0*deltay*lscale/(boxlen*ul)
     ymax = ycenter + 0.5d0*deltay*lscale/(boxlen*ul)
  endif
  if(deltaz > 0.0d0)then
     zmin = zcenter - 0.5d0*deltaz*lscale/(boxlen*ul)
     zmax = zcenter + 0.5d0*deltaz*lscale/(boxlen*ul)
  endif
  
  !-----------------------
  ! Map parameters
  !-----------------------
  if(lmax==0)then
     lmax=nlevelmax
  endif
  ncpu_read=ncpu
  do j=1,ncpu
     cpu_list(j)=j
  end do

  !-----------------------------------------------
  ! Compute projected variables
  !----------------------------------------------
  icell = 0
  istep = 10
  iprog = 1
  ! Loop over processor files
  if(.not. quiet) write(*,'(a,i5,a)')'Processing ',ncpu_read,' files in '//trim(repository)
  do k=1,ncpu_read
  
     if(.not. quiet)then
         percentage = nint(real(k)*100.0/real(ncpu_read))
         if(percentage .ge. iprog*istep)then
            write(*,'(i3,a,i9,a)') percentage,'% : read',icell,' cells'
            iprog = iprog + 1
         endif
     endif
  
     icpu=cpu_list(k)
     write(ncharcpu,'(i5.5)') icpu

     ! Open AMR file and skip header
     nomfich=TRIM(repository)//'/amr_'//TRIM(nchar)//'.out'//TRIM(ncharcpu)
     open(unit=10,file=nomfich,status='old',form='unformatted')
     do i=1,21
        read(10)
     end do
     ! Read grid numbers
     read(10)ngridlevel
     ngridfile(1:ncpu,1:nlevelmax)=ngridlevel
     read(10)
     if(nboundary>0)then
        do i=1,2
           read(10)
        end do
        read(10)ngridbound
        ngridfile(ncpu+1:ncpu+nboundary,1:nlevelmax)=ngridbound
     endif
     read(10)
     read(10)
     read(10)
     read(10)
     read(10)
     read(10)

     ! Open HYDRO file and skip header
     nomfich=TRIM(repository)//'/hydro_'//TRIM(nchar)//'.out'//TRIM(ncharcpu)
     open(unit=11,file=nomfich,status='old',form='unformatted')
     read(11)
     read(11)
     read(11)
     read(11)
     read(11)
     read(11)
     
     ! Loop over levels
     do ilevel=1,lmax

        ! Geometry
        dx=0.5d0**ilevel
        dx2=0.5d0*dx
        do ind=1,twotondim
           iz=(ind-1)/4
           iy=(ind-1-4*iz)/2
           ix=(ind-1-2*iy-4*iz)
           xc(ind,1)=(dble(ix)-0.5d0)*dx
           xc(ind,2)=(dble(iy)-0.5d0)*dx
           xc(ind,3)=(dble(iz)-0.5d0)*dx
        end do

        ! Allocate work arrays
        ngrida=ngridfile(icpu,ilevel)
        if(ngrida>0)then
           allocate(xg (1:ngrida,1:3))
           allocate(son(1:ngrida,1:twotondim))
           allocate(var(1:ngrida,1:twotondim,1:nvarh+5))
           allocate(x  (1:ngrida,1:3))
           allocate(ref(1:ngrida))
           x  = 0.0d0
           xg = 0.0d0
        endif

        ! Loop over domains
        do j=1,nboundary+ncpu

           ! Read AMR data
           if(ngridfile(j,ilevel)>0)then
              read(10) ! Skip grid index
              read(10) ! Skip next index
              read(10) ! Skip prev index
              ! Read grid center
              do n=1,ndim
                 if(j.eq.icpu)then
                    read(10)xg(:,n)
                 else
                    read(10)
                 endif
              end do
              read(10) ! Skip father index
              do ind=1,2*ndim
                 read(10) ! Skip nbor index
              end do
              ! Read son index
              do ind=1,twotondim
                 if(j.eq.icpu)then
                    read(10)son(:,ind)
                 else
                    read(10)
                 end if
              end do
              ! Skip cpu map
              do ind=1,twotondim
                 read(10)
              end do
              ! Skip refinement map
              do ind=1,twotondim
                 read(10)
              end do
           endif

           ! Read HYDRO data
           read(11)
           read(11)
           if(ngridfile(j,ilevel)>0)then
              ! Read hydro variables
              do ind=1,twotondim
                 do ivar=1,nvarh
                    if(j.eq.icpu)then
                       read(11)var(:,ind,ivar)
                    else
                       read(11)
                    end if
                 end do
              end do
           end if
        end do

        ! Compute map
        if(ngrida>0)then

           ! Loop over cells
           do ind=1,twotondim

              ! Compute cell center
              do i=1,ngrida
                 do n = 1,ndim
                    x(i,n)=(xg(i,n)+xc(ind,n)-xbound(n))
                 enddo
              end do
              ! Check if cell is refined
              do i=1,ngrida
                 ref(i)=son(i,ind)>0.and.ilevel<lmax
              end do
              ! Store data cube
              do i=1,ngrida
                ok_cell= .not.ref(i).and. &
                     & (x(i,1)+dx2)>=xmin.and.&
                     & (x(i,2)+dx2)>=ymin.and.&
                     & (x(i,3)+dx2)>=zmin.and.&
                     & (x(i,1)-dx2)<=xmax.and.&
                     & (x(i,2)-dx2)<=ymax.and.&
                     & (x(i,3)-dx2)<=zmax

                 if(ok_cell)then
                 
                    icell = icell + 1
                    
                    if(icell > nmax)then
                       write(*,'(a)') 'Not enough memory space, increase nmaxcells or decrease lmax.'
                       failed = .true.
                       return
                    endif
                 
                    var(i,ind,nvarh+1) = real(ilevel)
                    var(i,ind,nvarh+2) = x(i,1)*boxlen
                    var(i,ind,nvarh+3) = x(i,2)*boxlen
                    var(i,ind,nvarh+4) = x(i,3)*boxlen
                    var(i,ind,nvarh+5) = dx*boxlen
                    
                    jvar = 0
                    do ivar = 1,nvarh+5
                       if(ok_read(ivar))then
                          jvar = jvar + 1
                          data_array(icell,jvar) = var(i,ind,ivar)
                       endif
                    enddo
                                        
                 end if
              end do

           end do
           ! End loop over cell

           deallocate(xg,son,var,ref,x)
        endif

     end do
     ! End loop over levels

     close(10)
     close(11)

  end do
  ! End loop over cpus
  ncells = icell
  if(.not. quiet) write(*,'(a,i10,a)') 'Total number of cells loaded: ',ncells
  deallocate(ok_read)

  return
  
end subroutine ramses_data

!=============================================================================
! Quick scanning of the amr structure to find the highest level with at least
! 1 grid.
!=============================================================================
subroutine quick_amr_scan(infile,lmax2,xcenter,ycenter,zcenter,deltax,deltay,deltaz,lscale,&
                        & ud,ul,ut,active_lmax,nmaxcells,failed)

  implicit none
  
  ! Subroutine arguments
  character(LEN=*), intent(in ) :: infile
  integer         , intent(in ) :: lmax2
  real*8          , intent(in ) :: xcenter,ycenter,zcenter,deltax,deltay,deltaz,lscale,ud,ul,ut
  
  integer         , intent(out) :: active_lmax,nmaxcells
  logical         , intent(out) :: failed
  
  ! Variables
  integer :: ncpu,ndim,levelmin,levelmax,ngrid_current
  integer :: i,j,k,n,twotondim,nboundary
  integer :: nx,ny,nz,ilevel,nlevelmax,lmax,ind,ipos,ngrida
  integer :: ngridmax,icpu,ncpu_read,ix,iy,iz
  integer, dimension(:  ), allocatable :: cpu_list
  integer, dimension(:,:), allocatable :: son,ngridfile,ngridlevel,ngridbound
  
  real*8 :: xmin,xmax,ymin,ymax,zmin,zmax,boxlen,dx,dx2
  real*8, dimension(:,:    ), allocatable :: x,xg
  real*8, dimension(1:8,1:3)              :: xc
  real*8, dimension(    1:3)              :: xbound
  
  character(LEN=5  ) :: nchar,ncharcpu
  character(LEN=50 ) :: string
  character(LEN=128) :: nomfich,repository
  
  logical :: ok,ok_cell
  logical, dimension(:), allocatable :: ref
  
  !=============================================================================

  failed = .false.
  lmax = lmax2
  repository = trim(infile)
  xmin=0.0d0
  xmax=1.0d0
  ymin=0.0d0
  ymax=1.0d0
  zmin=0.0d0
  zmax=1.0d0
  xbound=(/0.0d0,0.0d0,0.0d0/)

  !-----------------------------------------------
  ! Reading RAMSES data
  !-----------------------------------------------
  ipos=INDEX(repository,'output_')
  nchar=repository(ipos+7:ipos+13)
  nomfich=TRIM(repository)//'/amr_'//TRIM(nchar)//'.out00001'
  inquire(file=nomfich, exist=ok) ! verify input file 
  if ( .not. ok ) then
     write(*,'(a)') TRIM(nomfich)//' not found.'
     failed = .true.
     return
  endif

  nomfich=TRIM(repository)//'/amr_'//TRIM(nchar)//'.out00001'
  open(unit=10,file=nomfich,status='old',form='unformatted')
  read (10) ncpu
  read (10) ndim
  read (10) nx,ny,nz
  read (10) nlevelmax
  read (10) ngridmax
  read (10) nboundary
  read (10) ngrid_current
  read (10) boxlen
  close(10)
  twotondim=2**ndim
  xbound=(/dble(nx/2),dble(ny/2),dble(nz/2)/)
  
  allocate(ngridfile(1:ncpu+nboundary,1:nlevelmax))
  allocate(ngridlevel(1:ncpu,1:nlevelmax))
  if(nboundary>0)allocate(ngridbound(1:nboundary,1:nlevelmax))
  allocate(cpu_list(1:ncpu))
  
  !-----------------------
  ! Map parameters
  !-----------------------
  if(lmax==0)then
     lmax=nlevelmax
  endif
  ncpu_read=ncpu
  do j=1,ncpu
     cpu_list(j)=j
  end do
  
  if(deltax > 0.0d0)then
     xmin = xcenter - 0.5d0*deltax*lscale/(boxlen*ul)
     xmax = xcenter + 0.5d0*deltax*lscale/(boxlen*ul)
  endif
  if(deltay > 0.0d0)then
     ymin = ycenter - 0.5d0*deltay*lscale/(boxlen*ul)
     ymax = ycenter + 0.5d0*deltay*lscale/(boxlen*ul)
  endif
  if(deltaz > 0.0d0)then
     zmin = zcenter - 0.5d0*deltaz*lscale/(boxlen*ul)
     zmax = zcenter + 0.5d0*deltaz*lscale/(boxlen*ul)
  endif
  
  nmaxcells = 0

  do k=1,ncpu_read
  
     icpu=cpu_list(k)
     write(ncharcpu,'(i5.5)') icpu

     ! Open AMR file and skip header
     nomfich=TRIM(repository)//'/amr_'//TRIM(nchar)//'.out'//TRIM(ncharcpu)
     open(unit=10,file=nomfich,status='old',form='unformatted')
     do i=1,21
        read(10)
     end do
     ! Read grid numbers
     read(10)ngridlevel
     ngridfile(1:ncpu,1:nlevelmax)=ngridlevel
     read(10)
     if(nboundary>0)then
        do i=1,2
           read(10)
        end do
        read(10)ngridbound
        ngridfile(ncpu+1:ncpu+nboundary,1:nlevelmax)=ngridbound
     endif
     read(10)
     read(10)
     read(10)
     read(10)
     read(10)
     read(10)

     ! Loop over levels
     do ilevel=1,lmax
     
        ! Geometry
        dx=0.5d0**ilevel
        dx2=0.5d0*dx
        do ind=1,twotondim
           iz=(ind-1)/4
           iy=(ind-1-4*iz)/2
           ix=(ind-1-2*iy-4*iz)
           xc(ind,1)=(dble(ix)-0.5d0)*dx
           xc(ind,2)=(dble(iy)-0.5d0)*dx
           xc(ind,3)=(dble(iz)-0.5d0)*dx
        end do

!       Allocate work arrays
        ngrida=ngridfile(icpu,ilevel)
        if(ngrida>0)then
           allocate(xg (1:ngrida,1:3))
           allocate(son(1:ngrida,1:twotondim))
           allocate(x  (1:ngrida,1:3))
           allocate(ref(1:ngrida))
           x  = 0.0d0
           xg = 0.0d0
        endif

        ! Loop over domains
        do j=1,nboundary+ncpu

           ! Read AMR data
           if(ngridfile(j,ilevel)>0)then
              read(10) ! Skip grid index
              read(10) ! Skip next index
              read(10) ! Skip prev index
              ! Read grid center
              do n=1,ndim
                 if(j.eq.icpu)then
                    read(10)xg(:,n)
                 else
                    read(10)
                 endif
              end do
              read(10) ! Skip father index
              do ind=1,2*ndim
                 read(10) ! Skip nbor index
              end do
              ! Read son index
              do ind=1,twotondim
                 if(j.eq.icpu)then
                    read(10)son(:,ind)
                 else
                    read(10)
                 end if
              end do
              ! Skip cpu map
              do ind=1,twotondim
                 read(10)
              end do
              ! Skip refinement map
              do ind=1,twotondim
                 read(10)
              end do
           endif
           
        end do
        
        ! Compute map
        if(ngrida>0)then
        
           active_lmax = ilevel

           ! Loop over cells
           do ind=1,twotondim

              ! Compute cell center
              do i=1,ngrida
                 do n = 1,ndim
                    x(i,n)=(xg(i,n)+xc(ind,n)-xbound(n))
                 enddo
              end do
              ! Check if cell is refined
              do i=1,ngrida
                 ref(i)=son(i,ind)>0.and.ilevel<lmax
              end do
              ! Store data cube
              do i=1,ngrida
                ok_cell= .not.ref(i).and. &
                     & (x(i,1)+dx2)>=xmin.and.&
                     & (x(i,2)+dx2)>=ymin.and.&
                     & (x(i,3)+dx2)>=zmin.and.&
                     & (x(i,1)-dx2)<=xmax.and.&
                     & (x(i,2)-dx2)<=ymax.and.&
                     & (x(i,3)-dx2)<=zmax

                 if(ok_cell) nmaxcells = nmaxcells + 1
                 
              enddo
           enddo
           
           deallocate(xg,son,ref,x)
           
        endif

     end do
     ! End loop over levels

     close(10)

  end do
  ! End loop over cpus
  
  return

end subroutine quick_amr_scan
