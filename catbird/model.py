from copy import deepcopy
from .collection import MooseCollection
from .factory import Factory
from .syntax import get_relation_kwargs

# TODO should this also be a MooseCollection?
class MooseModel():
    """Class to represent a MOOSE model"""
    def __init__(self,factory_in):
        assert isinstance(factory_in,Factory)
        self.factory=factory_in
        #self.moose_objects={}

        # Add attributes to this model with default assignments
        self.load_default_syntax()

    # Envisage this being overridden downstream.
    def load_default_syntax(self):
        self.add_syntax("Executioner", obj_type="Steady")
        self.add_syntax("Executioner.Predictor",obj_type="AdamsPredictor")
        #self.add_syntax("Problem", obj_type="FEProblem")
        #self.add_syntax("Mesh", obj_type="GeneratedMesh")
        self.add_syntax("Mesh",
                        obj_type="GeneratedMesh",
                        action="CreateDisplacedProblemAction")
        #self.add_syntax("Variables")

    #def  add_category(self, category, category_type, syntax_name=""):
    # # Ensure this is valid syntax
        # if category not in self.factory.constructors.keys():
        #     msg="Invalid block type {}".format(category)
        #     raise RuntimeError(msg)

        # # First look up the syntax type
        # syntax_type=self.factory.available_blocks[category].syntax_type

        # # How to add depends on syntax type
        # if syntax_type == "fundamental":
        #     # If fundmantal, just add. We're done.
        #     self.add_object(category,category_type)
        # elif syntax_type == "nested":
        #     if not hasattr(self,category):
        #         self.add_collection(category)
        #     self.add_to_collection(category,category_type,syntax_name)
        # elif syntax_type == "system":
        #     raise NotImplementedError()
        # elif syntax_type == "nested_system":
        #     raise NotImplementedError()
        # else:
        #     msg="Unhandled syntax type {}".format(syntax_type)
        #     raise RuntimeError(msg)

        # # Object has been constructed, now just book-keeping
        # category_key=category.lower()
        # if category_key not in self.moose_objects.keys():
        #     self.moose_objects[category_key]=list()
        # self.moose_objects[category_key].append(category_type)

    def add_syntax(self,syntax_name,**kwargs_in):
        """
        Add an object corresponding to MOOSE syntax
        """
        # First, pop out any relation key-word args
        obj_types={}
        relations=get_relation_kwargs()
        kwargs=deepcopy(kwargs_in)
        for keyword in kwargs_in.keys():
            if keyword in relations:
                obj_type = kwargs.pop(keyword)
                obj_types[keyword]=obj_type

        # Construct the object
        obj=self.factory.construct_root(syntax_name,obj_types,kwargs)

        # Add to model
        self._add_to_model(obj)

    def _add_to_model(self,obj):
        """Add object to the model as an attribute"""
        # Obtain sequence of objects
        obj_classname=obj.__class__.__name__
        obj_path=obj_classname.split(sep=".")

        # Attribute name (non-capitalised)
        obj_name=obj_path.pop(-1)
        attr_name=obj_name.lower()

        # Recurse through parent attribute objects
        parent_obj=self
        while len(obj_path)>0:
            new_parent_name=obj_path.pop(-1)
            new_parent_name=new_parent_name.lower()
            if not hasattr(parent_obj,new_parent_name):
                msg="Cannot construct {}:\n".format(syntax_name)
                msg=msg+"Class {} has no attribute {}".format(parent_obj.__class__.__name__,new_parent_name)
                raise RuntimeError(msg)
            new_parent_obj=getattr(parent_obj,new_parent_name)
            parent_obj=new_parent_obj

        # Avoid overwriting
        if hasattr(parent_obj,attr_name):
            msg="Class {} already has attribute {}".format(parent_obj.__class__.__name__,attr_name)
            raise RuntimeError(msg)

        # Add as attribute
        setattr(parent_obj,attr_name,obj)

        # If the parent is a collection, add there for book-keeping purposes
        # N.B. this is to support subblock syntax
        if isinstance(parent_obj,MooseCollection):
            parent_obj.add(obj,attr_name)

    # def add_collection(self, collection_type):
    #     # E.g. Variables, Kernels, BCs, Materials
    #     # Create new subclass of with a name that matches the collection_type
    #     new_cls = type(collection_type, (MOOSECollection,), dict())

    #     # Prefer non-capitalised attributes
    #     attr_name=collection_type.lower()

    #     # Construct and add the to model
    #     setattr(self, attr_name, new_cls())

    # def add_to_collection(self, collection_type, object_type, syntax_name, **kwargs):
    #     raise NotImplementedError

    #     # Construct object
    #     obj=self.factory.construct(collection_type,object_type,**kwargs)
    #     if syntax_name=="":
    #         raise RuntimeError("Must supply syntax_name for nested syntax")

    #     obj.set_syntax_name(syntax_name)

    #     # Obtain the object for this collection type
    #     collection = getattr(self, collection_type.lower())

    #     # Store in collection
    #     collection.add(obj)

    # # Some short-hands for common operations
    # def add_variable(self,name,variable_type="MooseVariable"):
    #     raise NotImplementedError
    #     #self.add_category("Variables",variable_type,name)

    # def add_bc(self):
    #     raise NotImplementedError

    # def add_ic(self):
    #     raise NotImplementedError

    # def to_str(self,print_default=False):
    #     model_str=""
    #     for obj_type in self.moose_objects:
    #         obj=getattr(self,obj_type)
    #         model_str+=obj.to_str(print_default)
    #     return model_str

    # def write(self, filename):
    #     file_handle = open(filename,'w')
    #     file_handle.write(self.to_str())
    #     file_handle.close()
    #     print("Wrote to ",filename)
