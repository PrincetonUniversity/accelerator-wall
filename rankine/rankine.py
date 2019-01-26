from optparse import OptionParser
import math
import sys
import numpy as np

# Rankine is a tool that models the CMOS-driven potentials of a monolithic silicon chip. It is named after the Scottish physicist Willian Rankine, which was the first to introduce the term: "potential energy"[1].
# We used Rankine for the accelerator evaluations in our paper:
# "The Accelerator Wall: Limits of Chip Specialization" A. Fuchs and D. Wentzlaff, 2019 IEEE International Symposium on High Performance Computer Architecture (HPCA)
#
# Rankine receives as input the physical characteristics of a chip and returns the chip's potential functions derived from the provided characteristics.
# The possible functions are: throughput, throughput per energy, throughput per area, throughput per cost, etc.
# One can derive other functions using the tool's output combine with other interesting target functions.
# The purpose of this tool is to provide an insight of physical scaling trends. 
# Therefore, and much like traditional potential functions, while the absolute output nubmers are meaningless, they are useful when comparing two or more subejcts (i.e., chips.) 
# 
# METHODOLOGY:
# CMOS Device Scaling: We combined the scaling numbers from contemporary circuit-level characterization study[2] with projections from the most recent IRDS report[3].   
# CMOS Cost Scaling: We leveraged two recent studies CMOS manufacturing costs [4,5] 
# Chip transistor count and thermal design power modeling: we leveraged linear regression based on datapoints extracted from datasheets of thousands of commercial processors [6,7,8]

# References:
# [1] https://en.wikipedia.org/wiki/William_John_Macquorn_Rankine
# [2] Stillmaker, Aaron, and Bevan Baas. "Scaling equations for the accurate prediction of CMOS device performance from 180 nm to 7 nm." Integration, the VLSI Journal 58 (2017): 74-81.
# [3] IRDS, "International roadmap for devices and systems (irds) 2017 edition." https://irds.ieee.org/roadmap-2017
# [4] Jones, Handel ,"FD SOI Benefits Rise at 14nm",EE times https://www.eetimes.com/author.asp?section_id=36&doc_id=1329887
# [5] Khazraee, Moein, et al. "Moonwalk: NRE optimization in ASIC clouds." ASPLOS 2017
# [6] Danowitz, Andrew, et al. "CPU DB: recording microprocessor history." ACM Queue 2012
# [7] TechPowerUp, "GPU database" https://www.techpowerup.com/gpudb, July 2018
# [8] TechPowerUp, "CPU database" https://www.techpowerup.com/cpudb, July 2018 

RANKINE_VERSION = 0.1

# Device scaling models
cmos_energy_fj = {}
cmos_energy_fj[180] = 27.5
cmos_energy_fj[150] = 11.96
cmos_energy_fj[130] = 5.2
cmos_energy_fj[110] = 3.69
cmos_energy_fj[90] = 2.62
cmos_energy_fj[80] = 2.12
cmos_energy_fj[65] = 1.72
cmos_energy_fj[55] = 1.34
cmos_energy_fj[45] = 1.05
cmos_energy_fj[40] = 1.0
cmos_energy_fj[32] = 0.51
cmos_energy_fj[28] = 0.45
cmos_energy_fj[22] = 0.3
cmos_energy_fj[20] = 0.2
cmos_energy_fj[16] = 0.18
cmos_energy_fj[14] = 0.14
cmos_energy_fj[12] = 0.13
cmos_energy_fj[10] = 0.12
cmos_energy_fj[7] = 0.11
cmos_energy_fj[5] = 0.1
cmos_dynamic_power_uw = {}
cmos_dynamic_power_uw[180] = 356.22
cmos_dynamic_power_uw[150] = 231.04
cmos_dynamic_power_uw[130] = 149.86
cmos_dynamic_power_uw[110] = 121.72
cmos_dynamic_power_uw[90] = 98.87
cmos_dynamic_power_uw[80] = 92.67
cmos_dynamic_power_uw[65] = 86.87
cmos_dynamic_power_uw[55] = 91.48
cmos_dynamic_power_uw[45] = 96.33
cmos_dynamic_power_uw[40] = 94.34
cmos_dynamic_power_uw[32] = 52.04
cmos_dynamic_power_uw[28] = 46.39
cmos_dynamic_power_uw[22] = 30.84
cmos_dynamic_power_uw[20] = 20.5
cmos_dynamic_power_uw[16] = 29.25
cmos_dynamic_power_uw[14] = 35.82
cmos_dynamic_power_uw[12] = 36.73
cmos_dynamic_power_uw[10] = 37.65
cmos_dynamic_power_uw[7] = 44.94
cmos_dynamic_power_uw[5] = 46.83
cmos_leakage_power_uw = {}
cmos_leakage_power_uw[180] = 105.0
cmos_leakage_power_uw[150] = 50.0
cmos_leakage_power_uw[130] = 26.1
cmos_leakage_power_uw[110] = 18.42
cmos_leakage_power_uw[90] = 13.0
cmos_leakage_power_uw[80] = 10.56
cmos_leakage_power_uw[65] = 8.58
cmos_leakage_power_uw[55] = 6.67
cmos_leakage_power_uw[45] = 5.19
cmos_leakage_power_uw[40] = 5.0
cmos_leakage_power_uw[32] = 2.47
cmos_leakage_power_uw[28] = 2.13
cmos_leakage_power_uw[22] = 1.79
cmos_leakage_power_uw[20] = 1.51
cmos_leakage_power_uw[16] = 1.28
cmos_leakage_power_uw[14] = 0.99
cmos_leakage_power_uw[12] = 0.93
cmos_leakage_power_uw[10] = 0.87
cmos_leakage_power_uw[7] = 0.79
cmos_leakage_power_uw[5] = 0.72
cmos_latency_ps = {}
cmos_latency_ps[180] = 77.2
cmos_latency_ps[150] = 51.76
cmos_latency_ps[130] = 34.7
cmos_latency_ps[110] = 30.32
cmos_latency_ps[90] = 26.5
cmos_latency_ps[80] = 22.91
cmos_latency_ps[65] = 19.8
cmos_latency_ps[55] = 14.69
cmos_latency_ps[45] = 10.9
cmos_latency_ps[40] = 10.6
cmos_latency_ps[32] = 9.8
cmos_latency_ps[28] = 9.7
cmos_latency_ps[22] = 9.68
cmos_latency_ps[20] = 9.66
cmos_latency_ps[16] = 6.12
cmos_latency_ps[14] = 4.02
cmos_latency_ps[12] = 3.61
cmos_latency_ps[10] = 3.24
cmos_latency_ps[7] = 2.47
cmos_latency_ps[5] = 2.16
cmos_vdd_v = {}
cmos_vdd_v[180] = 1.8
cmos_vdd_v[150] = 1.47
cmos_vdd_v[130] = 1.2
cmos_vdd_v[110] = 1.15
cmos_vdd_v[90] = 1.1
cmos_vdd_v[80] = 1.1
cmos_vdd_v[65] = 1.05
cmos_vdd_v[55] = 1.01
cmos_vdd_v[45] = 0.97
cmos_vdd_v[32] = 0.97
cmos_vdd_v[28] = 0.93
cmos_vdd_v[22] = 0.92
cmos_vdd_v[20] = 0.9
cmos_vdd_v[16] = 0.88
cmos_vdd_v[14] = 0.86
cmos_vdd_v[12] = 0.8
cmos_vdd_v[10] = 0.75
cmos_vdd_v[7] = 0.7
cmos_vdd_v[5] = 0.65

# CMOS manufacturing costs
cmos_cost = {}
cmos_cost[150] = 7.91
cmos_cost[130] = 5.63
cmos_cost[110] = 4.75
cmos_cost[90] = 4.01
cmos_cost[65] = 2.82
cmos_cost[55] = 2.34
cmos_cost[45] = 1.94
cmos_cost[40] = 1.94
cmos_cost[32] = 1.94
cmos_cost[28] = 1.3
cmos_cost[22] = 1.67
cmos_cost[20] = 1.54
cmos_cost[16] = 1.43
cmos_cost[14] = 1.43
cmos_cost[10] = 1.45
cmos_cost[7] = 1.52
cmos_cost[5] = 1.65


# Transistor count curve. the curve was constructed using datasheets from thousands of commercial processors.
# given the die area and cmos node nm, the number of die transistors is approximately: 
# count = np.exp(transistors_count_curve[1])*density_factor**(transistors_count_curve[0])
transistors_count_curve = [0.87650569, 22.33031902]
  
# Effective transistors calculation curve under power restrictions. The curves were constructed based on datasheets from thousands of commercial processors.
# Given the TDP, cmos node and chip frequency the effective number of transistors is approximately: 
# count = (np.exp(power_restricted_transistor_count_curves[node][1])*tdp_w**(power_restricted_transistor_count_curves[node][0]))/float(frequency_ghz)
power_restricted_transistor_count_curves = {}
power_restricted_transistor_count_curves[150] = [1.35608520112,14.175921764] # 180nm-150nm
power_restricted_transistor_count_curves[65] = [1.0858064719,15.4524644369] # 130nm-65nm
power_restricted_transistor_count_curves[40] = [0.869396475567,16.8439598602] # 55nm-40nm
power_restricted_transistor_count_curves[28] = [0.728781502506,18.4867193491] # 32nm-28nm
power_restricted_transistor_count_curves[12] = [0.557376653843,20.0141471218] # 22nm-12nm
power_restricted_transistor_count_curves[5] = [0.401658287972,21.4891760308] # 10nm-5nm

def transistor_count_from_die_size(transistors_count_curve, die_area_mm2, cmos_node_nm):
  density_factor = float(die_area_mm2)/float(cmos_node_nm*cmos_node_nm) # The theoretical number of transistors that fit on a die should be proportional to: die_area /(feature_size^2) 
  return np.exp(transistors_count_curve[1])*density_factor**(transistors_count_curve[0])

def effective_transistor_count_from_tdp(power_restricted_transistor_count_curves,cmos_node_nm,frequency_mhz,tdp_w):
  # Computes the number of effective transistors out of the chip thermal design power
  coef = None
  for k in sorted(power_restricted_transistor_count_curves.keys())[::-1]:
    if cmos_node_nm >= k:
      coef = power_restricted_transistor_count_curves[k]
      break
  assert(coef!=None) # should not happen
  frequency_ghz = frequency_mhz/1e3
  return (np.exp(coef[1])*tdp_w**(coef[0]))/float(frequency_ghz)
  


def cmos_potential_calculation(die_area_mm2,cmos_node_nm,transistor_count_mil,tdp_w,frequency_mhz):
  transistors = None 
  if not transistor_count_mil is None:
    transistors = transistor_count_mil*1e6 
  else:  
    transistors = transistor_count_from_die_size(transistors_count_curve, die_area_mm2, cmos_node_nm)
  tdp_transistors = effective_transistor_count_from_tdp(power_restricted_transistor_count_curves,cmos_node_nm,frequency_mhz,tdp_w)
  num_transistors_constraint = min(tdp_transistors,transistors)
  cmos_device_frequency_mhz = 1e6/float(cmos_latency_ps[cmos_node_nm])
  throughput = num_transistors_constraint*float(frequency_mhz)
  transistor_static_power = cmos_leakage_power_uw[cmos_node_nm]*1e-6
  transistor_dynamic_power = cmos_dynamic_power_uw[cmos_node_nm]*float(frequency_mhz)/float(cmos_device_frequency_mhz)*1e-6 # down scaling (from full device level frequency to chip frequency)  
  transistor_power =(transistor_dynamic_power+transistor_static_power) 
  power = (num_transistors_constraint*transistor_dynamic_power) + (transistors*transistor_static_power)
  cost = None
  if cmos_node_nm in cmos_cost:
    cost = transistors*cmos_cost[cmos_node_nm]
  return (throughput, transistors, cost, power)
   

def count_string(count):
  if count >= 1e9:
    return "{0} Billion".format(round(count/1e9,2))
  if count >= 1e6:
    return "{0} Million".format(round(count/1e6,2))
  if count >= 1e3:
    return "{0}K".format(round(count/1e3,2))
    

def print_summary(options, throughput, transistors, cost, power):
  delay = 1.0/throughput
  energy = power*delay
  throughput_per_power = throughput/power
  edp = energy*delay 
  ed2p = edp*delay

  print "**************************************************************************"
  print "              RANKINE v{0}: A CMOS Potential Modeling Tool ".format(RANKINE_VERSION)
  print "**************************************************************************"
  print "                                 REPORT"
  print "**************************************************************************"
  if options.die_area_mm2:
     print "{0}mm^2".format(options.die_area_mm2),
  print "{0}nm chip".format(options.cmos_node_nm), 
  print "with {0} transistors clocked at: {1}MHz.".format(count_string(transistors), options.frequency_mhz)
  print "The thermal design power is: {0}W.".format(options.tdp_w)  
  print "**************************************************************************"
  print " 			     Potential Factors"
  print "**************************************************************************"
  print "Throughput: {0}".format(throughput)
  print "Throughput per Power: {0}".format(throughput_per_power)
  if options.die_area_mm2:
    print "Throughput per Area: {0}".format(throughput/(options.die_area_mm2))
    print "Throughput per Power per Area: {0}".format(throughput_per_power/(options.die_area_mm2))
  if not (cost is None):
    print "Throughput per Cost: {0}".format(throughput/cost)
  print "Energy: {0}".format(energy)  
  print "EDP: {0}".format(edp)  
  print "ED^2P: {0}".format(ed2p)  
    

def supported_range_warning(var, range_min,range_max, var_name, var_units):
  if (var < range_min or var > range_max) and (not (var is None)):
    print "WARNING: out of the evaluted processor datasheets, only few (or none) had a {0} of {1}{2}. The generated factors are the result of extrapolation (hence accuracy might be affected)".format(var_name,var, var_units)
    
  
  
if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option("-n", "--cmos-node-nm", dest="cmos_node_nm", metavar="<node>",type="int", help="CMOS Techology Node [nm]")
  parser.add_option("-c", "--transistor-count", dest="transistor_count_mil", metavar="<count>" ,type="int", help="Chip transistor count [millions] (mandatory if die area is not provided)")
  parser.add_option("-a", "--die-area", dest="die_area_mm2", metavar="<area>", type="float", help="Chip die area[mm^2] (mandatory if transistor count is not provided)")
  parser.add_option("-t", "--thermal-design-power", dest="tdp_w", metavar="<power>", type="float", help="Chip thermal design power (TDP)[W]")
  parser.add_option("-f", "--chip-frequency", dest="frequency_mhz", metavar="<freq>", type="float", help="Chip frequency [MHz]")
  (options, args) = parser.parse_args()
  
  # Checking for required argunments
  for [option, opt_str] in zip([options.cmos_node_nm,options.tdp_w,options.frequency_mhz],["CMOS node", "TDP", "Frequency"]):
    if not option:
      print opt_str + " was not provided."
      parser.print_help()
      sys.exit(1)
  if not options.transistor_count_mil and not options.die_area_mm2:
    print "please provide either chip transistor count or chip die area."
    parser.print_help()
    sys.exit(1)  
  print   
  if options.cmos_node_nm not in cmos_latency_ps.keys():
    print "Unsupported CMOS node {0}nm. Supported nodes are: {1}".format(options.cmos_node_nm, ",".join([str(s) for s in sorted(cmos_latency_ps.keys())]))
    sys.exit(1)
  supported_range_warning(options.tdp_w, 1.0,300.0, "TDP", "W")
  supported_range_warning(options.cmos_node_nm, 10.0,180.0, "CMOS node", "nm")
  supported_range_warning(options.frequency_mhz, 50.0,3000.0, "frequency", "MHz")
  supported_range_warning(options.die_area_mm2, 10.0,600.0, "die area", "mm2")
  (throughput, transistors, cost, power) = cmos_potential_calculation(options.die_area_mm2,options.cmos_node_nm,options.transistor_count_mil,options.tdp_w,options.frequency_mhz)
  print_summary(options, throughput, transistors, cost, power)

  
  
  
