import re

def snake_case(name: str):
    """
    https://stackoverflow.com/a/1176023/1371716
    """
    name = re.sub('(\\.)', r'_', name)
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('__([A-Z])', r'_\1', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower()

def capfirst(value: str):
    return value[:1].upper() + value[1:]

def simple_singular(value: str):
    if value.endswith('ies'):
        return value[:-3] + 'y'
    elif value.endswith('s'):
        return value[:-1]
    else:
        return value

def safe_enum_name(value: str):
    """Convert a string to a valid Python identifier for enum member names.
    
    Replaces dots, hyphens, and other invalid characters with underscores.
    """
    # Replace dots and hyphens with underscores
    safe_name = re.sub(r'[.\-]', '_', value)
    # Replace any other non-alphanumeric characters (except underscore) with underscore
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_name)
    # Ensure it doesn't start with a digit
    if safe_name and safe_name[0].isdigit():
        safe_name = '_' + safe_name
    return safe_name
        