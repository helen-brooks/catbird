[Mesh]
  file = mesh.e
[]

[AuxVariables]
  [Temperature]
    initial_condition = 500
  []
  [H3_source]
    initial_condition = 1e-12
  []
  # summary variables for nicer output quantities in SI units
  [total_trapped]
  []
  [total_mobile]
  []
  [total_retention]
  []
[]

[AuxKernels]
  [total_mobile]
    type = ParsedAux
    variable = total_mobile
    coupled_variables = 'mobile'
    expression = 'mobile * 6.3222e28'
  []
  [total_trapped]
    type = ParsedAux
    variable = total_trapped
    coupled_variables = 'trapped_1 trapped_2'
    expression = '(trapped_1 + trapped_2) * 6.3222e28'
  []
  [total_retention]
    type = ParsedAux
    variable = total_retention
    coupled_variables = 'mobile trapped_1 trapped_2'
    expression = '(mobile + trapped_1 + trapped_2) * 6.3222e28'
  []
[]

[Functions]
[]

# ---------------------------------------------------#
#
#  define nonlinear variables
#  (optional FE shape function and order,
#   defaults to first order lagrange)
#
# ---------------------------------------------------#

[Variables]
  [mobile]
  []
  [trapped_1]
  []
  [trapped_2]
  []
[]


# ---------------------------------------------------#
#
#  material properties for each material block
#
# ---------------------------------------------------#

# each material property needs repeating for each material block in the mesh
# but the property names should be the same i.e.
# `property_name = D` for each block for e.g [D_steel], [D_tungsten] etc.
# I've commented out a block restriction option on each property it will be needed on
# if you're using a multi-block model.

[Materials]
  [D]
    type = ADParsedMaterial
    property_name = 'D'
    coupled_variables = 'Temperature'
    constant_names = 'D0 E kb'
    constant_expressions = '4.1e-7 0.39 8.6e-5'
    expression = 'D0 * exp(-E / (kb * Temperature))'
    #block = W
  []

  [trapping_factor_W_1]
    type = ADParsedMaterial
    property_name = 'trapping_rate_1'
    coupled_variables = 'Temperature'
    constant_names = 'k0 E kb rho'
    constant_expressions = '8.96e-17 0.39 8.6e-5 6.3222e28'
    expression = 'k0 * rho * exp(-E / (kb * Temperature))'
    #block = W
  []
  [trapping_factor_W_2]
    type = ADParsedMaterial
    property_name = 'trapping_rate_2'
    coupled_variables = 'Temperature'
    constant_names = 'k0 E kb rho'
    constant_expressions = '8.96e-17 0.39 8.6e-5 6.3222e28'
    expression = 'k0 * rho * exp(-E / (kb * Temperature))'
    #block = W
  []

  [detrapping_factor_W_1]
    type = ADParsedMaterial
    property_name = 'detrapping_rate_1'
    coupled_variables = 'Temperature'
    constant_names = 'p0 E kb'
    constant_expressions = '1e13 0.87 8.6e-5'
    expression = '-p0 * exp(-E / (kb * Temperature))'
    #block = W
  []
  [detrapping_factor_W_2]
    type = ADParsedMaterial
    property_name = 'detrapping_rate_2'
    coupled_variables = 'Temperature'
    constant_names = 'p0 E kb'
    constant_expressions = '1e13 1.0 8.6e-5'
    expression = '-p0 * exp(-E / (kb * Temperature))'
    #block = W
  []

  [trap_density_W_1]
    type = ADParsedMaterial
    property_name = 'trap_density_1'
    constant_names = 'n'
    constant_expressions = '1.3e-3'
    expression = 'n'
    #block = W
  []
  [trap_density_W_2]
    type = ADParsedMaterial
    property_name = 'trap_density_2'
    constant_names = 'n'
    constant_expressions = '4e-4'
    expression = 'n'
    #block = W
  []

  [atomic_density_W]
    type = ADGenericConstantMaterial
    prop_names = 'rho'
    prop_values = '6.3222e28'
    #block = W
  []

  [trap_1_reaction]
    type = ADParsedMaterial
    coupled_variables = trapped_1
    property_name = 'trap_1_reaction'
    material_property_names = 'trapping_rate_1 trap_density_1'
    expression = 'trapping_rate_1 * (trap_density_1 - trapped_1)'
  []
  [trap_2_reaction]
    type = ADParsedMaterial
    property_name = 'trap_2_reaction'
    coupled_variables = trapped_2
    material_property_names = 'trapping_rate_2 trap_density_2'
    expression = 'trapping_rate_2 * (trap_density_2 - trapped_2)'
  []
[]

# ---------------------------------------------------#
#
#  physics kernels
#  defines the system of coupled PDEs
#
# ---------------------------------------------------#

[Kernels]

# these kernels describe the mobile species transport and trapping
  [time_derivative_mobile]
    type = ADTimeDerivative
    variable = mobile
  []
  [source_term]
    type = ADCoupledForce
    variable = mobile
    v = H3_source
  []
  [diffusion]
    type = ADMatDiffusion
    variable = mobile
    diffusivity = D
  []
  [coupled_time_derivative_trap_1]
    type = ADCoupledTimeDerivative
    variable = mobile
    v = trapped_1
  []
  [coupled_time_derivative_trap_2]
    type = ADCoupledTimeDerivative
    variable = mobile
    v = trapped_2
  []

# this pattern repeats for each trap type in the simulation (2 here)
  [time_derivative_trap_1]
    type = ADTimeDerivative
    variable = trapped_1
  []
  [trapping_1]
    type = ADMatReaction
    variable = trapped_1
    v = mobile
    reaction_rate = trap_1_reaction
  []
  [detrapping_1]
    type = ADMatReaction
    variable = trapped_1
    reaction_rate = detrapping_rate_1
  []

  [time_derivative_trap_2]
    type = ADTimeDerivative
    variable = trapped_2
  []
  [trapping_2]
    type = ADMatReaction
    variable = trapped_2
    v = mobile
    reaction_rate = trap_2_reaction
  []
  [detrapping_2]
    type = ADMatReaction
    variable = trapped_2
    reaction_rate = detrapping_rate_2
  []

[]

# ---------------------------------------------------#
#
#           Apply all boundary conditions
#     (reflection implied by default for mobile species)
#
# ---------------------------------------------------#

[BCs]
  [outflow]
    type = ADDirichletBC
    variable = mobile
    boundary = 'Steel_Helium Steel_air Beryllium_air SteelMaybe_air Tungsten_air'
    value = 0
  []
[]

# ---------------------------------------------------#
#
# Numerical solver and simulation parameters
#
# ---------------------------------------------------#

[Executioner]
  type = Transient
  solve_type = NEWTON

  # convergence criteria
#  nl_abs_tol = 3e-13
#  nl_rel_tol = 1e-7
#  nl_max_its = 20


  # numerical solver parameters
  #petsc_options_iname = '-ksp_type -pc_type -pc_factor_mat_solver_type -pc_factor_shift_type'
  #petsc_options_value = 'bcgs lu mumps NONZERO'
  #petsc_options_iname = '-ksp_type -pc_type -pc_hypre_type -pc_factor_shift_type'
  #petsc_options_value = 'bcgs hypre boomeramg NONZERO'
  petsc_options_iname = '-ksp_type -pc_type -pc_factor_mat_solver_package -pc_factor_shift_type'
  petsc_options_value = 'bcgs lu superlu_dist NONZERO'

  line_search= l2
  scheme = bdf2

  automatic_scaling=true
  compute_scaling_once=false
  residual_and_jacobian_together = true
  reuse_preconditioner = true
  reuse_preconditioner_max_linear_its = 20

  # timestepping options
  [TimeStepper]
    type = IterationAdaptiveDT
    optimal_iterations = 12
    cutback_factor = 0.8
    growth_factor = 1.2
    dt = 10
  []
  end_time = 1e5
  dtmin=1e-2
  #dtmax = 1e3
[]

# ---------------------------------------------------#
#
# Output options
#
# ---------------------------------------------------#

[Postprocessors]
# total surface fluxes into all gas volumes
  [cooling_surface_flux]
   type = ADSideDiffusiveFluxIntegral
    variable = total_mobile
    boundary = 'Steel_Helium Steel_air Beryllium_air SteelMaybe_air Tungsten_air'
    diffusivity = D
  []

# can also output fluxes across specific solid boundaries
  [interface_flux_W_Cu]
    type = ADInterfaceDiffusiveFluxIntegral
    variable = total_mobile
    diffusivity = D
    boundary = Beryllium_Tungsten
  []

# total retention requires an achlys postprocessor
#  [total_mobile]
#    type = VariableIntegral
#    variable = total_mobile
#  []
#  [total_retention]
#    type = VariableIntegral
#    variable = total_retention
#  []


[Outputs]
  console = true
  exodus = true
  csv = true
[]
