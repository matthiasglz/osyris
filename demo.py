import matplotlib.pyplot as plt
import numpy as np
import osiris as pp
import sys

# Load data
mydata = pp.RamsesData(nout=71,center="auto",scale="au")

# Create figure
fig = plt.figure()
ratio = 0.5
sizex = 20.0
fig.set_size_inches(sizex,ratio*sizex)
ax1 = fig.add_subplot(231)
ax2 = fig.add_subplot(232)
ax3 = fig.add_subplot(233)
ax4 = fig.add_subplot(234)
ax5 = fig.add_subplot(235)
ax6 = fig.add_subplot(236)

dx = 100

# Density vs B field with AMR level contours
mydata.plot_histogram("log_rho","log_B",var_z="level",axes=ax1,cmap="YlGnBu")

# Create new field
mydata.new_field(name="log_vel",operation="np.log10(np.sqrt(velocity_x**2+velocity_y**2+velocity_z**2))",unit="cm/s",label="log(Velocity)")

# Density vs log_vel
mydata.plot_histogram("log_rho","log_vel",axes=ax2,cmap="YlGnBu")

#x,z density slice with B field streamlines
mydata.plot_slice("log_rho",direction="y",stream="B",dx=dx,axes=ax3)
# x,y density slice with velocity vectors in color
mydata.plot_slice("log_rho",direction="z",vec="velocity",dx=dx,axes=ax4,vskip=4,vcmap="Greys")
# x,y temperature slice with velocity vectors
mydata.plot_slice("log_T",direction="z",vec="velocity",dx=dx,axes=ax5,cmap="hot")

# Now update values with later snapshot
mydata.update_values(201)
# Re-plot x,y density slice with velocity vectors in color
mydata.plot_slice("log_rho",direction="z",vec="velocity",dx=100,axes=ax6)

fig.savefig("demo.pdf",bbox_inches="tight")
