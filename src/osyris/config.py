# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2019 Osyris contributors (https://github.com/nvaytet/osyris)
# @author Neil Vaytet

# from matplotlib.colors import LinearSegmentedColormap
# import matplotlib.pyplot as plt
# import numpy as np

#==============================================================================
# Define default values so that you don't have to specify them every time.
#==============================================================================
config = {
    "length_scale"       : "au" ,
    "time_scale"   : "kyr",
    "path"        : ""   ,
    "variables"   : []   ,
    "colormap"    : "viridis"
}


def additional_units(ureg):
    ureg.define('solar_mass = 1.9889e+33 * g = msun')
    ureg.define('radiation_constant = 7.56591469318689378e-015 * erg / cm^3 / K^4 = ar')

# #==============================================================================
# # Define default units for some selected variables. The syntax is:
# # "my_variable_name" : ["combination of unit_d, unit_l, unit_t" , "string to be displayed on grid axes"]
# #==============================================================================
# default_units = {
#     ## Example for internal energy
#     #"passive_scalar_4" : ["unit_d*((unit_l/unit_t)**2)" , "erg/cm3"],
# }

# #==============================================================================
# # Physical constants
# #==============================================================================
# constants = {
#     "cm"  : 1.0,
#     "au"  : 1.495980e+13,
#     "pc"  : 3.085678e+18,
#     "s"   : 1.0,
#     "yr"  : 365.25*86400.0,
#     "kyr" : 365.25*86400.0*1000.0,
#     "msun": 1.9889e33,
#     "a_r" : 7.56591469318689378e-015,
#     "c"   : 2.9979250e+10
# }

# #==============================================================================
# # Custom colormaps
# #==============================================================================
# cmaps = {
#     "osyris"  : ["#2b3c4e", "#249593", "#db6a6c", "#ffffff"],
#     "osyris2" : ["#2b3c4e", "#249593", "#ffffff", "#db6a6c", "#9e4d4e"],
#     "osyris3" : ["#3d3d6b", "#2a7b9b", "#00baad", "#57c785", "#add45c",
#                  "#ffc300", "#ff8d1a", "#ff5733", "#c70039", "#900c3f",
#                  "#511849"],
#     "osyris4" : ["#000000", "#ff5b00", "#ffff00", "#00ff00", "#2bc184",
#                  "#3d3d6b", "#ffffff", "#0000ff"],
#     "osyris5" : ["#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff0000",
#                  "#000000", "#ffffff"]
# }

# for key in cmaps.keys():
#     cmap = LinearSegmentedColormap.from_list(key, cmaps[key])
#     cmap_r = LinearSegmentedColormap.from_list(key+"_r", cmaps[key][::-1])
#     plt.register_cmap(cmap=cmap)
#     plt.register_cmap(cmap=cmap_r)


def additional_variables(data):
    """
    Here are some additional variables that are to be computed every time data
    is loaded.
    """

    try:
        # Magnetic field
        data["B_field"] = 0.5 * (data["B_left"] + data["B_right"])

        # Mass
        data["mass"] = data["dx"]*data["dx"]*data["dx"] * data["density"]
        data["mass"].to("msun")
    except KeyError:
        pass

    #========================== ADD YOUR VARIABLES HERE ============================

