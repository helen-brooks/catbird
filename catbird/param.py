class MooseParam():
    """
    Class to contain all information about a MOOSE parameter

    Attributes:

      allowed_vals:
        If set, list of allowed values for this parameter.
      attr_type:
        Type of this parameter.
      controllable (bool)  :
        Indicates if this parameter may be controlled by a MOOSE Control object.
      default:
        Default value for this parameter.
      description (str):
        Short description for this parameter.
      doc (str):
        Documentation for this parameter.
      is_array (bool):
        Indicates if this parameter is iterable.
      name:
        Name of this parameter.
      required
        Whether it is mandatory to set this parameter in the owning class.
      val
        Current value of this parameter.
    """
    def __init__(self,attr_name, attr_type, is_array, default=None, allowed_vals=None, required=False, controllable=False, description=None):

        assert attr_type is not type(None)

        self.attr_type=attr_type
        self.allowed_vals=allowed_vals
        self.is_array=is_array

        # Set name
        if not isinstance(attr_name, str):
            raise ValueError('Attribute names must be strings')
        self.name=attr_name

        # Set default value
        if default is not None:
            self.default=default
        elif self.is_array and attr_type!=str:
            self.default=[attr_type()]
        else:
            self.default=attr_type()

        # Initialise current value to the default
        self.val=self.default

        self.required=required
        self.controllable=controllable

        self.description=description

        # Set docstring
        doc_str = '\n'
        doc_str += attr_name+' : '
        doc_str += f'{attr_type.__name__}\n'
        if description is not None and description != "":
            doc_str += "  "
            doc_str += description
            doc_str += "\n"
        if allowed_vals is not None:
            doc_str += f'  Allowed values: {allowed_vals}\n'
        if default is not None:
            doc_str += f'  Default value: {default}\n'
        doc_str += f'  Required: {required}\n'
        self.doc=doc_str
