!pip install pyomo
from pyomo.opt import SolverManagerFactory, SolverFactory
import pyomo.environ as pyo
import pandas as pd
import math
from math import log10
import os
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'



model = pyo.ConcreteModel()



FLOW = float(input("Enter the value of Flow rate in KL/Hr : "))
KV = float(input("Enter the value of Kinematic Viscosity of Crude oil at 15 deg C in cSt : "))
rho = float(input("Enter the value of Density of Crude oil at 15 deg C in kg/m3 : "))
SFC_J = float(input("Enter SFC at 100% load of Engine in Jamnagar in gm/bhp/hr : "))
SFC_R = float(input("Enter SFC at 100% load of Engine in Rajkot in gm/bhp/hr : "))
SFC_S = float(input("Enter SFC at 100% load of Engine in Surendranagar in gm/bhp/hr : "))
RateDRA = float(input("Enter unit rate of DRA in Rs/Litre : "))
Price_HSD = float(input("Enter unit rate of HSD fuel in Rs/Litre : "))


# Vadinar-Jamnagar (Vadinar 4 Motor driven MLPUs)
model.FLOW1=pyo.Param(initialize = FLOW)
FLOW1 = model.FLOW1
model.D1 = pyo.Param(initialize = 0.7112)
D1 = model.D1
model.t1 = pyo.Param(initialize = 0.0071374)
t1 = model.t1
model.SMYS1 = pyo.Param(initialize = 52000)
SMYS1 = model.SMYS1
model.KV1 = pyo.Param(initialize = KV)
KV1 = model.KV1
model.e1 = pyo.Param(initialize = 0.00004)
e1 = model.e1
model.rho1 = pyo.Param(initialize = rho)
rho1 = model.rho1
model.L1 = pyo.Param(initialize = 46.7)
L1 = model.L1
model.z1 = pyo.Param(initialize = 8)
z1 = model.z1
model.d1 = pyo.Param(initialize = 0.697)
d1 = model.d1
model.DF1 = pyo.Param(initialize = 0.72)
DF1 = model.DF1
model.Rate1 = pyo.Param(initialize = 9)
Rate1 = model.Rate1
model.A1 = pyo.Param(initialize = -0.000002)
A1 = model.A1
model.B1 = pyo.Param(initialize = -0.0015)
B1 = model.B1
model.C1 = pyo.Param(initialize = 179.14)
C1 = model.C1
model.DOL1 = pyo.Param(initialize = 1500)
DOL1 = model.DOL1
model.MinRPM1 = pyo.Param(initialize = 1200)
MinRPM1 = model.MinRPM1
model.BEP1 = pyo.Param(initialize = 4000)
BEP1 = model.BEP1
model.P1 = pyo.Param(initialize = -4.161E-14)
P1 = model.P1
model.Q1 = pyo.Param(initialize = 6.574E-10)
Q1 = model.Q1
model.R1 = pyo.Param(initialize = -0.000008737)
R1 = model.R1
model.S1 = pyo.Param(initialize = 0.04924)
S1 = model.S1
model.T1 = pyo.Param(initialize = -0.001754)
T1 = model.T1
model.RH1 = pyo.Param(initialize = 50)
RH1 = model.RH1
model.Rate_DRA = pyo.Param(initialize = RateDRA)
Rate_DRA = model.Rate_DRA
model.z2 = pyo.Param(initialize = 24)
z2 = model.z2 #Elevation at Jamnagar


# Jamnagar-Rajkot(Jamnagar 3 Engine driven MLPUs)
model.FLOW2 = pyo.Param(initialize = FLOW)
FLOW2 = model.FLOW2
model.D2 = pyo.Param(initialize = 0.7112)
D2 = model.D2
model.t2 = pyo.Param(initialize = 0.0071374)
t2 = model.t2
model.SMYS2 = pyo.Param(initialize = 52000)
SMYS2 = model.SMYS2
model.KV2 = pyo.Param(initialize = KV)
KV2 = model.KV2
model.e2 = pyo.Param(initialize = 0.00004)
e2 = model.e2
model.rho2 = pyo.Param(initialize = rho)
rho2 = model.rho2
model.L2 = pyo.Param(initialize = 67.9)
L2 = model.L2
model.d2 = pyo.Param(initialize = 0.697)
d2 = model.d2
model.DF2 = pyo.Param(initialize = 0.72)
DF2 = model.DF2
model.SFC2 = pyo.Param(initialize = SFC_J)
SFC2 = model.SFC2
model.A2 = pyo.Param(initialize = -1*10**-5)
A2 = model.A2
model.B2 = pyo.Param(initialize = 0.00135)
B2 = model.B2
model.C2 = pyo.Param(initialize = 270.08)
C2 = model.C2
model.DOL2 = pyo.Param(initialize = 3437)
DOL2 = model.DOL2
model.MinRPM2 = pyo.Param(initialize = 2750)
MinRPM2 = model.MinRPM2
model.BEP2 = pyo.Param(initialize = 3150)
BEP2 = model.BEP2
model.P2 = pyo.Param(initialize = -4.07033296*10**-13)
P2 = model.P2
model.Q2 = pyo.Param(initialize = 3.4657688*10**-9)
Q2 = model.Q2
model.R2 = pyo.Param(initialize = -1.92727273*10**-5)
R2 = model.R2
model.S2 = pyo.Param(initialize = 6.7033189*10**-2)
S2 = model.S2
model.T2 = pyo.Param(initialize = -1.504329*10**-1)
T2 = model.T2
model.Rate_DRA = pyo.Param(initialize = RateDRA)
Rate_DRA = model.Rate_DRA
model.z3 = pyo.Param(initialize = 113)
z3 = model.z3 #Elevation at Rajkot



# Rajkot-Chotila
model.FLOW3 = pyo.Param(initialize = FLOW)
FLOW3 = model.FLOW3
model.D3 = pyo.Param(initialize = 0.7112)
D3 = model.D3
model.t3 = pyo.Param(initialize = 0.0071374)
t3 = model.t3
model.SMYS3 = pyo.Param(initialize = 52000)
SMYS3 = model.SMYS3
model.KV3 = pyo.Param(initialize = KV)
KV3 = model.KV3
model.e3 = pyo.Param(initialize = 0.00004)
e3 = model.e3
model.rho3 = pyo.Param(initialize = rho)
rho3 = model.rho3
model.L3 = pyo.Param(initialize = 40.2)
L3 = model.L3
model.d3 = pyo.Param(initialize = 0.697)
d3 = model.d3
model.DF3 = pyo.Param(initialize = 0.72)
DF3 = model.DF3
model.SFC3 = pyo.Param(initialize = SFC_R)
SFC3 = model.SFC3
model.A3 = pyo.Param(initialize = -1*10**-5)
A3 = model.A3
model.B3 = pyo.Param(initialize = 0.0192)
B3 = model.B3
model.C3 = pyo.Param(initialize = 218.81)
C3 = model.C3
model.DOL3 = pyo.Param(initialize = 2870)
DOL3 = model.DOL3
model.MinRPM3 = pyo.Param(initialize = 2296)
MinRPM3 = model.MinRPM3
model.BEP3 = pyo.Param(initialize = 2850)
BEP3 = model.BEP3
model.P3 = pyo.Param(initialize = -9.01972569E-13)
P3 = model.P3
model.Q3 = pyo.Param(initialize = 0.00000000745948934)
Q3 = model.Q3
model.R3 = pyo.Param(initialize = -0.0000319133266)
R3 = model.R3
model.S3 = pyo.Param(initialize = 0.0815595446)
S3 = model.S3
model.T3 = pyo.Param(initialize = -0.00303811075)
T3 = model.T3
model.Rate_DRA = pyo.Param(initialize = RateDRA)
Rate_DRA = model.Rate_DRA
model.z4 = pyo.Param(initialize = 232)
z4 = model.z4 #Elevation at Chotila


# Chotila-Surendranagar
model.FLOW4 = pyo.Param(initialize = FLOW)
FLOW4 = model.FLOW4
model.D4 = pyo.Param(initialize = 0.7112)
D4 = model.D4
model.t4 = pyo.Param(initialize = 0.0071374)
t4 = model.t4
model.SMYS4 = pyo.Param(initialize = 52000)
SMYS4 = model.SMYS4
model.KV4 = pyo.Param(initialize = KV)
KV4 = model.KV4
model.e4 = pyo.Param(initialize = 0.00004)
e4 = model.e4
model.rho4 = pyo.Param(initialize = rho)
rho4 = model.rho4
model.L4 = pyo.Param(initialize = 60)
L4 = model.L4
model.d4 = pyo.Param(initialize = 0.697)
d4 = model.d4
model.DF4 = pyo.Param(initialize = 0.72)
DF4 = model.DF4
model.Rate_DRA = pyo.Param(initialize = RateDRA)
Rate_DRA = model.Rate_DRA
model.z5 = pyo.Param(initialize = 80)
z5 = model.z5 #Elevation at Surendranagar


# Surendranagar-Viramgam
model.FLOW5 = pyo.Param(initialize = FLOW)
FLOW5 = model.FLOW5
model.D5 = pyo.Param(initialize = 0.7112)
D5 = model.D5
model.t5 = pyo.Param(initialize = 0.0071374)
t5 = model.t5
model.SMYS5 = pyo.Param(initialize = 52000)
SMYS5 = model.SMYS5
model.KV5 = pyo.Param(initialize = KV)
KV5 = model.KV5
model.e5 = pyo.Param(initialize = 0.00004)
e5 = model.e5
model.rho5 = pyo.Param(initialize = rho)
rho5 = model.rho5
model.L5 = pyo.Param(initialize = 60)
L5 = model.L5
model.d5 = pyo.Param(initialize = 0.697)
d5 = model.d5
model.DF5 = pyo.Param(initialize = 0.72)
DF5 = model.DF5
model.SFC5 = pyo.Param(initialize = SFC_S)
SFC5 = model.SFC5
model.A5 = pyo.Param(initialize = -1*10**-5)
A5 = model.A5
model.B5 = pyo.Param(initialize = 0.0229)
B5 = model.B5
model.C5 = pyo.Param(initialize = 183.59)
C5 = model.C5
model.DOL5 = pyo.Param(initialize = 3437)
DOL5 = model.DOL5
model.MinRPM5 = pyo.Param(initialize = 2750)
MinRPM5 = model.MinRPM5
model.BEP5 = pyo.Param(initialize = 2700)
BEP5 = model.BEP5
model.P5 = pyo.Param(initialize = -7.24279835*10**-13)
P5 = model.P5
model.Q5 = pyo.Param(initialize = 5.08093278*10**-9)
Q5 = model.Q5
model.R5 = pyo.Param(initialize = -0.0000249506173)
R5 = model.R5
model.S5 = pyo.Param(initialize = 0.0768906526)
S5 = model.S5
model.T5 = pyo.Param(initialize = -0.0912698413)
T5 = model.T5
model.Rate_DRA = pyo.Param(initialize = RateDRA)
Rate_DRA = model.Rate_DRA
model.z6 = pyo.Param(initialize = 23)
z6 = model.z6 #Elevation at Viramgam




# Decision Variables
# Vadinar
model.NOP1 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (1, 3))
NOP1 = model.NOP1
model.DR1 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (0, 40))
DR1 = model.DR1
model.N1 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (MinRPM1, DOL1))
N1 = model.N1
model.RH2 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (50, None))
RH2 = model.RH2 # RH2 is the RH at Jamnagar

# Jamnagar
model.NOP2 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (0, 2))
NOP2 = model.NOP2
model.DR2 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (0, 40))
DR2 = model.DR2
model.N2 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (MinRPM2, DOL2))
N2 = model.N2
model.RH3 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (50, None))
RH3 = model.RH3 # RH3 is the RH at Rajkot

# Rajkot
model.NOP3 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds =(0, 2))
NOP3 = model.NOP3
model.DR3 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (0, 40))
DR3 = model.DR3
model.N3 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (MinRPM3, DOL3))
N3 = model.N3
model.RH4 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (50, None))
RH4 = model.RH4 # RH4 is the RH at Chotila peak

# Chotila
model.RH5 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (50, None))
RH5 = model.RH5 # RH5 is the RH at Surendranagar

# Surendranagar
model.NOP5 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (0, 2))
NOP5 = model.NOP5
model.DR4 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (0, 40))
DR4 = model.DR4
model.N5 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (MinRPM5, DOL5))
N5 = model.N5
model.RH6 = pyo.Var(domain = pyo.NonNegativeIntegers, bounds = (50, None))
RH6 = model.RH6 # RH6 is the RH at Viramgam




# Equations
# Vadinar-Jamnagar
MAOP1=(2*t1*(SMYS1*0.070307)*DF1/D1)*10000/rho1
v1=FLOW1/2/(3.414*d1*d1/4)/3600
Re1=v1*d1/(KV1*10**-6)
f1=(0.25/(log10((e1/d1/3.7)+(5.74/(Re1**0.9))))**2)
SH1=RH2+(z2-z1)
DH1=(f1*(L1*1000/d1)*(v1**2/(2*9.81)))*(1-DR1/100)
SDHR_1=SH1+DH1
TDHA_PUMP_1=((A1*FLOW1**2)+(B1*FLOW1)+C1)*(N1/DOL1)**2
SDHA_1=RH1+(TDHA_PUMP_1)*NOP1
EFFM1=0.95
PPM1=DR1/4


# Jamnagar-Rajkot
MAOP2=(2*t2*(SMYS2*0.070307)*DF2/D2)*10000/rho2
v2=FLOW2/2/(3.414*d2*d2/4)/3600
Re2=v2*d2/(KV2*10**-6)
f2=(0.25/(log10((e2/d2/3.7)+(5.74/(Re2**0.9))))**2)
SH2=RH3+(z3-z2)
DH2=(f2*(L2*1000/d2)*(v2**2/(2*9.81)))*(1-DR2/100)
SDHR_2=SH2+DH2
TDHA_PUMP_2=((A2*FLOW2**2)+(B2*FLOW2)+C2)*(N2/DOL2)**2
SDHA_2=RH2+(TDHA_PUMP_2)*NOP2
EFFM2=0.95
PPM2=DR2/4


# Rajkot-Chotila
MAOP3=(2*t3*(SMYS3*0.070307)*DF3/D3)*10000/rho3
v3=FLOW3/2/(3.414*d3*d3/4)/3600
Re3=v3*d3/(KV3*10**-6)
f3=(0.25/(log10((e3/d3/3.7)+(5.74/(Re3**0.9))))**2)
SH3=RH4+(z4-z3)
DH3=(f3*(L3*1000/d3)*(v3**2/(2*9.81)))*(1-DR3/100)
SDHR_3=SH3+DH3
TDHA_PUMP_3=((A3*FLOW3**2)+(B3*FLOW3)+C3)*(N3/DOL3)**2
SDHA_3=RH3+(TDHA_PUMP_3)*NOP3
EFFM3=0.95
PPM3=DR3/4


# Chotila-Surendranagar
MAOP4=(2*t4*(SMYS4*0.070307)*DF4/D4)*10000/rho4
v4=FLOW4/2/(3.414*d4*d4/4)/3600
Re4=v4*d4/(KV4*10**-6)
f4=(0.25/(log10((e4/d4/3.7)+(5.74/(Re4**0.9))))**2)
SH4=RH5+(z5-z4)
DH4=(f4*(L4*1000/d4)*(v4**2/(2*9.81)))*(1-DR3/100)
SDHR_4=SH4+DH4
SDHA_4=RH4
PPM4=PPM3


# Surendranagar-Viramgam
MAOP5=(2*t5*(SMYS5*0.070307)*DF5/D5)*10000/rho5
v5=FLOW5/2/(3.414*d5*d5/4)/3600
Re5=v5*d5/(KV5*10**-6)
f5=(0.25/(log10((e5/d5/3.7)+(5.74/(Re5**0.9))))**2)
SH5=RH6+(z6-z5)
DH5=(f5*(L5*1000/d5)*(v5**2/(2*9.81)))*(1-DR4/100)
SDHR_5=SH5+DH5
TDHA_PUMP_5=((A5*FLOW5**2)+(B5*FLOW5)+C5)*(N5/DOL5)**2
SDHA_5=RH5+(TDHA_PUMP_5)*NOP5
EFFM5=0.95
PPM5=DR4/4



FLOW1_EQUIV_VALUE = FLOW1*DOL1/N1
EFFP1 = (P1*(FLOW1_EQUIV_VALUE)**4+Q1*(FLOW1_EQUIV_VALUE)**3+R1*(FLOW1_EQUIV_VALUE)**2+S1*(FLOW1_EQUIV_VALUE)+T1)/100

FLOW2_EQUIV_VALUE = FLOW2*DOL2/N2
EFFP2 = (P2*(FLOW2_EQUIV_VALUE)**4+Q2*(FLOW2_EQUIV_VALUE)**3+R2*(FLOW2_EQUIV_VALUE)**2+S2*(FLOW2_EQUIV_VALUE)+T2)/100

FLOW3_EQUIV_VALUE = FLOW3*DOL3/N3
EFFP3 = (P3*(FLOW3_EQUIV_VALUE)**4+Q3*(FLOW3_EQUIV_VALUE)**3+R3*(FLOW3_EQUIV_VALUE)**2+S3*(FLOW3_EQUIV_VALUE)+T3)/100

FLOW5_EQUIV_VALUE = FLOW5*DOL5/N5
EFFP5 = (P5*(FLOW5_EQUIV_VALUE)**4+Q5*(FLOW5_EQUIV_VALUE)**3+R5*(FLOW5_EQUIV_VALUE)**2+S5*(FLOW5_EQUIV_VALUE)+T5)/100



# Objective Function
# Power and DRA Cost of Vadinar MLPUs:
OF_POWER_1= (rho1*FLOW1*9.81*TDHA_PUMP_1*NOP1)/(3600*1000*EFFP1*EFFM1)*24*Rate1
OF_DRA_1= (PPM1/10**6)*FLOW1*24*1000*Rate_DRA

# Fuel and DRA Cost of Jamnagar MLPUs:
OF_POWER_2= ((rho2*FLOW2*9.81*TDHA_PUMP_2*NOP2)/(3600*1000*EFFP2*EFFM2))*(SFC2*1.34102/1000/820)*1000*24*Price_HSD
OF_DRA_2= (PPM2/10**6)*FLOW2*24*1000*Rate_DRA

# Fuel and DRA Cost of Rajkot MLPUs:
OF_POWER_3= ((rho3*FLOW3*9.81*TDHA_PUMP_3*NOP3)/(3600*1000*EFFP3*EFFM3))*(SFC3*1.34102/1000/820)*1000*24*Price_HSD
OF_DRA_3= (PPM3/10**6)*FLOW3*24*1000*Rate_DRA

# Fuel and DRA Cost of Surendranagar MLPUs:
OF_POWER_4= ((rho5*FLOW5*9.81*TDHA_PUMP_5*NOP5)/(3600*1000*EFFP5*EFFM5))*(SFC5*1.34102/1000/820)*1000*24*Price_HSD
OF_DRA_4= (PPM5/10**6)*FLOW5*24*1000*Rate_DRA

def Objective_Rule(model):
  return (OF_POWER_1 + OF_DRA_1 + OF_POWER_2 + OF_DRA_2 + OF_POWER_3 + OF_DRA_3 + OF_POWER_4 + OF_DRA_4)
model.Objf = pyo.Objective(rule = Objective_Rule, sense = pyo.minimize)



# Constraints
# Vadinar
def Constraint1(model):
  return SDHA_1 >= SDHR_1
model.const1 = pyo.Constraint(rule = Constraint1)

def Constraint2(model):
  return MAOP1 >= SDHA_1
model.const2 = pyo.Constraint(rule = Constraint2)


# Jamnagar
def Constraint10(model):
  return SDHA_2 >= SDHR_2
model.const10 = pyo.Constraint(rule = Constraint10)

def Constraint11(model):
  return MAOP2 >= SDHA_2
model.const11 = pyo.Constraint(rule = Constraint11)


# Rajkot
def Constraint19(model):
  return SDHA_3 >= SDHR_3
model.const19 = pyo.Constraint(rule = Constraint19)

def Constraint20(model):
  return MAOP3 >= SDHA_3
model.const20 = pyo.Constraint(rule = Constraint20)


# Chotila
def Constraint28(model):
  return SDHA_4 >= SDHR_4
model.const28 = pyo.Constraint(rule = Constraint28)

def Constraint29(model):
  return MAOP4 >= SDHA_4
model.const29 = pyo.Constraint(rule = Constraint29)


# Surendranagar
def Constraint31(model):
  return SDHA_5 >= SDHR_5
model.const31 = pyo.Constraint(rule = Constraint31)

def Constraint32(model):
  return MAOP5 >= SDHA_5
model.const32 = pyo.Constraint(rule = Constraint32)


solver = SolverManagerFactory('neos')
results = solver.solve(model, opt='bonmin', tee=True)
results.write()

print(results)
print('Total Optimum Cost= ', model.Objf())
print('The No. of operating pumps at Vadinar = ', NOP1())
print('The percentage Drag reduction at Vadinar = ', DR1())
print('The operating speed of each Pump at Vadinar = ', N1())
print('The value of Residual Head at Jamnagar = ', RH2())
print('The value of SDH at Vadinar = ', SDHA_1())
print('Head developed by each pump at Vadinar = ', TDHA_PUMP_1())
print('Optimum Power Cost at Vadinar = ', OF_POWER_1())
print('Optimum DRA cost at Vadinar = ', OF_DRA_1())
print('Value of Pump Efficiency at Vadinar = ', EFFP1())


print('The No. of operating pumps at Jamnagar = ', NOP2())
print('The percentage Drag reduction at Jamnagar = ', DR2())
print('The operating speed of each Pump at Jamnagar = ', N2())
print('The value of Residual Head at Rajkot = ', RH3())
print('The value of SDH at Jamnagar = ', SDHA_2())
print('Head developed by each pump at Jamnagar = ', TDHA_PUMP_2())
print('Optimum Power Cost at Jamnagar = ', OF_POWER_2())
print('Optimum DRA cost at Jamnagar = ', OF_DRA_2())
print('Value of Pump Efficiency at Jamnagar = ', EFFP2())



print('The No. of operating pumps at Rajkot = ', NOP3())
print('The percentage Drag reduction at Rajkot = ', DR3())
print('The operating speed of each Pump at Rajkot = ', N3())
print('The value of Residual Head at Chotila = ', RH4())
print('The value of SDH at Rajkot = ', SDHA_3())
print('Head developed by each pump at Rajkot = ', TDHA_PUMP_3())
print('Optimum Power Cost at Rajkot = ', OF_POWER_3())
print('Optimum DRA cost at Rajkot = ', OF_DRA_3())
print('Value of Pump Efficiency at Rajkot = ', EFFP3())


print('The value of Residual Head at Surendranagar = ', RH5())


print('The No. of operating pumps at Surendranagar = ', NOP5())
print('The percentage Drag reduction at Surendranagar = ', DR4())
print('The operating speed of each Pump at Surendranagar = ', N5())
print('The value of Residual Head at Viramgam = ', RH6())
print('The value of SDH at Surendranagar = ', SDHA_5())
print('Head developed by each pump at Surendranagar = ', TDHA_PUMP_5())
print('Optimum Power Cost at Surendranagar = ', OF_POWER_4())
print('Optimum DRA cost at Surendranagar = ', OF_DRA_4())
print('Value of Pump Efficiency at Surendranagar = ', EFFP5())

