from catbird import *

# Universal gas constant ( J/(mol K) )
R_univ=8.31

# This is how we enable syntax
# Only enable what you need, or it runs slowly!
class SimpleBreederFactory(Factory):
    def set_defaults(self):
        # Dictionaries limit enabled syntax to exactly what is specified
        executioner_enable_dict={
            "obj_type": ["Steady"],
        }
        aux_kernel_enable_dict={
            "collection_type": ["ParsedAux"]
        }
        kernel_enable_dict={
            "collection_type": ["ADCoupledForce","ADMatDiffusion"]
        }
        material_enable_dict={
            "collection_type": ["ADParsedMaterial","ADGenericConstantMaterial"]
        }
        bcs_enable_dict={
            "collection_type": ["ADDirichletBC"]
        }
        ics_enable_dict={
            "collection_type": ["ConstantIC", "FunctionIC"]
        }
        pp_enable_dict={
            "collection_type": ["ADInterfaceDiffusiveFluxIntegral"]
        }
        function_enable_dict={
            "collection_type": ["ParsedFunction"]
        }

        self.enable_syntax("Executioner", executioner_enable_dict)
        self.enable_syntax("Problem")
        self.enable_syntax("Mesh")
        self.enable_syntax("Variables")
        self.enable_syntax("AuxVariables")
        self.enable_syntax("Kernels",kernel_enable_dict)
        self.enable_syntax("AuxKernels",aux_kernel_enable_dict)
        self.enable_syntax("Materials",material_enable_dict)
        self.enable_syntax("BCs", bcs_enable_dict)
        self.enable_syntax("ICs", ics_enable_dict)
        self.enable_syntax("Functions", function_enable_dict)
        self.enable_syntax("Postprocessors",pp_enable_dict)
        self.enable_syntax("Outputs")

# Simple data structure for diffusion material properties
# Diffusivity will be set as D=D0 exp(-E_d / RT)
class DiffusionMaterial():
    def __init__(self,name,D0=1.0,E_d=1.0):
        self.name=name
        # Units: m^2/2 J/mol
        self.D0=D0
        # Units: J/(mol K)
        self.E_d=E_d

# Data structure to enable easily changing parameters
class SimpleBreederInputs():
    def __init__(self):
        # Geometry (all units metres)
        self.void_radius=12e-3
        self.ring_thicknesses=(8e-3,8e-3,8e-3)
        self.block_side_len=88e-3
        self.pipe_len=100e-3
        self.num_rings = len(self.ring_thicknesses)

        # Mesh params
        self.mesh_density=1e3 # divisions per metre
        # Number of divisions around each quarter sector
        self.num_quadrant_divisions=10

        # Mesh metadata
        self.void_names=['inner_void','outer_void']

        # Associate materials with regions
        self.initialise_materials(['steel','breeder','steel'],
                                  ['inner_steel', 'breeder', 'outer_steel'])

        # Set source strength ( mols / m^3 / s )
        self.source_strength = 1e-5

        # Temperature as function of position
        self.temp_func='500 + 2000*z'

    def initialise_materials(self,material_names, block_names):
        assert len(material_names) == self.num_rings
        assert len(block_names) == self.num_rings
        self.block_names=block_names
        self.material_names=material_names
        self.materials={}
        self.mats_to_blocks={}
        for mat_name,block_name in zip(self.material_names,self.block_names):
            if mat_name not in self.materials.keys():
                # Initalise a new material. We can set the properties later
                self.materials[mat_name]=DiffusionMaterial(mat_name)
                self.mats_to_blocks[mat_name]=[]
            # Save which blocks have this material
            self.mats_to_blocks[mat_name].append(block_name)
                        

# This class represents the boilerplate input deck
class SimpleBreederModel(MooseModel):
    # Initialise the outer blocks
    def load_default_syntax(self):
        self.add_syntax("Executioner", obj_type="Steady")
        self.add_syntax("Problem", obj_type="FEProblem")
        self.add_syntax("Mesh")
        self.add_syntax("Variables")
        self.add_syntax("AuxVariables")
        self.add_syntax("ICs")
        self.add_syntax("Functions")
        self.add_syntax("Kernels")
        self.add_syntax("Materials")
        self.add_syntax("BCs")
        self.add_syntax("Postprocessors")
        self.add_syntax("Outputs", action="CommonOutputAction")

    def __init__(self,factory_in,inputs):
        super().__init__(factory_in)
        assert isinstance(factory_in,SimpleBreederFactory)
        # Populate blocks
        self._concretise_model(inputs)

    def _setup_mesh(self, inputs):
        # Compute radii of cocentric cylinders and number layers of mesh
        radii=[inputs.void_radius]
        radial_divisions=[1]
        for thickness in inputs.ring_thicknesses:
            radius_now=radii[-1]+thickness
            assert radius_now < inputs.block_side_len
            radii.append(radius_now)
            divisions=int(thickness * inputs.mesh_density)
            radial_divisions.append(divisions)

        # Polar divisions in each quadrant
        quadrant_sectors=[inputs.num_quadrant_divisions]*4

        # Axial divisions
        num_extrude_divs=int(inputs.pipe_len * inputs.mesh_density)

        # Metadata
        ring_blocks=[inputs.void_names[0]]
        ring_blocks.extend(inputs.block_names)
        background_name=inputs.void_names[1]
        all_blocks=ring_blocks.copy()
        all_blocks.append(background_name)

        # Save block name for breeder layer
        self.breeder_name=inputs.block_names[1]

        # Auto-generate sideset names on interfaces between materials
        self.outward_normal_interface_names=[]
        self.inward_normal_interface_names=[]
        num_interfaces=len(all_blocks)-1
        for i_block in range(num_interfaces):
            inner_name=all_blocks[i_block]
            outer_name=all_blocks[i_block+1]
            outward_interface_name=inner_name+"_"+outer_name
            inward_interface_name=outer_name+"_"+inner_name
            self.inward_normal_interface_names.append(inward_interface_name)
            self.outward_normal_interface_names.append(outward_interface_name)

        # Save names of boundaries to void (normals pointing into void)
        self.outflow_boundaries=[self.inward_normal_interface_names[0],
                                 self.outward_normal_interface_names[-1]]

        # Save names boundaries from middle breeder ring into adjacent materials
        self.breeder_boundaries=[self.inward_normal_interface_names[1],
                                 self.outward_normal_interface_names[-2]]

        # Construct a mesh using mesh generators
        mg_names=["polygon_rings","delete_inner","delete_outer","extrude","rename_boundaries","split_boundaries"]

        # Constructs some rings inside a square
        self.add_mesh_generator(mg_names[0],
                                "PolygonConcentricCircleMeshGenerator",
                                num_sides=4,
                                polygon_size=inputs.block_side_len,
                                polygon_size_style='apothem',
                                ring_radii=radii,
                                ring_intervals=radial_divisions,
                                ring_block_names=" ".join(ring_blocks),
                                num_sectors_per_side=quadrant_sectors,
                                background_intervals=1,
                                preserve_volumes='on',
                                flat_side_up=True,
                                background_block_names=background_name,
                                interface_boundary_id_shift = 1000,
                                external_boundary_name='outer',
                                generate_side_specific_boundaries=False,
                                create_inward_interface_boundaries=True,
                                create_outward_interface_boundaries=True,
                                inward_interface_boundary_names=" ".join(self.inward_normal_interface_names),
                                outward_interface_boundary_names=" ".join(self.outward_normal_interface_names))

        # Delete the void blocks (outer square and innermost ring)
        self.add_mesh_generator(mg_names[1],
                                "BlockDeletionGenerator",
                                input=mg_names[0],
                                block=inputs.void_names[0])

        self.add_mesh_generator(mg_names[2],
                                "BlockDeletionGenerator",
                                input=mg_names[1],
                                block=inputs.void_names[1])

        # Extrude our rings along z
        self.add_mesh_generator(mg_names[3],
                                "AdvancedExtruderGenerator",
                                input=mg_names[2],
                                direction='0 0 1',
                                heights=inputs.pipe_len,
                                num_layers=num_extrude_divs)

        # Set sensible outer boundary names
        self.add_mesh_generator(mg_names[4],
                                "RenameBoundaryGenerator",
                                input=mg_names[3],
                                old_boundary='1008 1009',
                                new_boundary='bottom top')

        self.add_mesh_generator(mg_names[5],
                                "BreakBoundaryOnSubdomainGenerator",
                                input=mg_names[4],
                                boundaries='bottom top')

    def _add_diffusion_material(self, mat, blocks):
        assert isinstance(mat,DiffusionMaterial)
        block_str=" ".join(blocks)
        self.add_material("D_{}".format(mat.name),
                          "ADParsedMaterial",
                          property_name='D',
                          coupled_variables=self.temp_name,
                          constant_names='D0 E_d R',
                          constant_expressions='{} {} {}'.format(mat.D0,mat.E_d,R_univ),
                          expression='D0 * exp(-E_d / (R * {}))'.format(self.temp_name),
                          block=block_str)


    def _concretise_model(self, inputs):
        assert isinstance(inputs,SimpleBreederInputs)

        # Define some MOOSE internal names for self-consistency
        self.var_name="concentration"
        self.temp_name="temperature"
        self.source_name="H3_source"
        self.temp_function_name="parsed_function"
        self.diffusivity_name="D"

        # Add mesh generators to construct the mesh
        self._setup_mesh(inputs)

        # Set executioner attributes
        self.executioner.solve_type='NEWTON'
        self.executioner.petsc_options_iname = '-pc_type -pc_factor_mat_solver_package'
        self.executioner.petsc_options_value = 'lu superlu_dist'
        self.executioner.line_search = 'none'

        # Add variable
        self.add_variable(self.var_name)

        # Add aux variables
        self.add_aux_variable(self.temp_name)
        self.add_aux_variable(self.source_name)

        # Initial condition for source term
        self.add_ic("source_ic",
                    "ConstantIC",
                    variable=self.source_name,
                    value=inputs.source_strength)

        # Initial condition for temperature
        self.add_ic("temp_ic",
                    "FunctionIC",
                    variable=self.temp_name,
                    function=self.temp_function_name)

        # Temperature function for initial condition
        self.add_function(self.temp_function_name,
                          "ParsedFunction",
                          expression=inputs.temp_func)

        # Add kernels to define diffusion
        self.add_kernel("diffusion",
                        kernel_type="ADMatDiffusion",
                        variable=self.var_name)
        self.add_kernel("source_term",
                        kernel_type="ADCoupledForce",
                        variable=self.var_name,
                        block=self.breeder_name,
                        v=self.source_name)
        
        # Add BCs
        outflow_boundary_str=" ".join(self.outflow_boundaries)
        self.add_bc("outflow",
                    "ADDirichletBC",
                    boundary=outflow_boundary_str,
                    value=0.0,
                    variable=self.var_name)

        # Add materials
        for mat_name, blocks in inputs.mats_to_blocks.items():
            mat=inputs.materials[mat_name]
            self._add_diffusion_material(mat, blocks)

        # Add postprocessors
        pp_boundary_str=" ".join(self.breeder_boundaries)
        self.add_postprocessor("diffusive_flux_integral",
                               "ADInterfaceDiffusiveFluxIntegral",
                               variable=self.var_name,
                               diffusivity=self.diffusivity_name,
                               boundary=pp_boundary_str)

        # Enable outputs
        self.outputs.csv=True
        self.outputs.exodus=True
