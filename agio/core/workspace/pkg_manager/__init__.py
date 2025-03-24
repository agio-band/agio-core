

def get_package_manager():
    from .uv import  UVPackageManager
    return UVPackageManager