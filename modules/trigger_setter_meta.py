"""MetClass which enforce running all setters at object creation"""
from modules.custom_exceptions import ConfigurationError


# Custom metaclass
class TriggerSetterMeta(type):
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)

        # if 'Configuration' in str(cls.__base__):
        #     __cls = cls.__base__
        # elif 'Configuration' in str(cls):
        #     __cls = cls
        # else:
        #     raise ValueError("Configuration class not found as being base class either main class")

        # Find dataclass fields
        dataclass_fields = [attr for attr, value in instance.__dataclass_fields__.items()]

        for field_name in dataclass_fields:
            if field_name.startswith('_'):
                continue  # Skip private attributes

            # Call the setter method for each dataclass field
            setter_name = f"_{field_name}_setter"
            if hasattr(instance, setter_name):
                setter = getattr(instance, setter_name)
                field_value = getattr(instance, field_name)
                setter(field_value)
            else:
                raise ConfigurationError
        return instance
