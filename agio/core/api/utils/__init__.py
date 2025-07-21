
NOTSET = type("NotSetSentinel", (), {
    "__repr__": lambda self: "<NOTSET>",
    "__bool__": lambda self: False,
    "__nonzero__": lambda self: False,
})()
