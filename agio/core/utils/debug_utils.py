def print_stack_simple(full_path=True, ignore_list=None):
    from fnmatch import fnmatch
    import traceback, sys, os

    pycharm_ignore_list = ['pydev*', 'code.py']
    ignore_list = ignore_list or []
    ignore_list.extend(pycharm_ignore_list)

    frame = sys._getframe().f_back
    stack = traceback.extract_stack(frame)[:-1]
    stack = [x for x in stack if not any([fnmatch(os.path.basename(x.filename), pat) for pat in ignore_list])]

    for i, item in enumerate(stack):
        path = item.filename if full_path else os.path.basename(item.filename)
        print(f"{' ' * i}{path}[{item.lineno}] -> {item.name}{'()' if not '>' in item.name else ''}")