from AST import *

def add_builtins(*builtins : BuiltinFunc):
    """Add a list of new built-in functions in all programs' global scope."""
    GlobalScope.builtins.extend(builtins)

def add_type(t : type, constructor_args : list[Arg | Varg] | None, attributes : set[str], methods : dict[str, list[Arg | Varg]]):
    """Add a new type, with its methods in all programs' context / global scope
    Args:
        t (type) : the type to add to all Robotica scripts.
        constructor_args (list[Arg | Varg] | None) : the type's constructor arguments. if None, will not add constructor.
        attributes (set[str]) : all accessible attributes of the type.
        methods (dict[str, list[Arg | Varg]]) : methods of the type. key = name of method, value = method arguments."""
    Context.types[t.__name__] = t
    if constructor_args != None:
        GlobalScope.builtins.append(BuiltinFunc(t.__name__, constructor_args, t, type=t))
    for m, args in methods.items():
        Context.methods[getattr(t, m)] = args
    Context.attributes[t] = attributes

def add_basic_types():
    add_type(int, [Arg("x"), Arg("base", int, 10)], {}, {})
    add_type(float, [Arg("x")], {}, {})
    add_type(bool, [Arg("x")], {}, {})
    add_type(str, [Arg("x")], {}, {
        "upper" : [],
        "lower" : [],
        "format": [Varg("args")],
        "join"  : [Arg("elems", list)],
        "split" : [Arg("sep", str), Arg("max_split", int, Nothing())],
        "isalpha": [],
        "isalnum": [],
        "isnumeric": [],
        "isidentifier": [],
    })
    add_type(list, [Arg("iter", value=Nothing())], {}, {
        "clear" : [],
        "copy" : [],
        "count" : [Arg("value")],
        "append" : [Arg("elem")],
        "extend" : [Arg("l", list)],
        "index" : [Arg("value")],
        "insert" : [Arg("value"), Arg("index", int)],
        "pop" : [Arg("index", int)],
        "remove" : [Arg("value")],
        "reverse" : [],
        "sort" : []
    })
    add_type(set, [], {}, {
        "add" : [Arg("value")],
        "clear" : [],
        "copy" : [],
        "difference" : [Varg("others")],
        "difference_update" : [Varg("others")],
        "discard" : [Arg("element")],
        "intersection" : [Varg("others")],
        "intersection_update" : [Varg("others")],
        "isdisjoint" : [Arg("other", set)],
        "issubset" : [Arg("other", set)],
        "issuperset" : [Arg("other", set)],
        "pop" : [],
        "remove" : [Arg("value")],
        "symmetric_difference" : [Varg("others")],
        "symmetric_difference_update" : [Varg("others")],
        "union" : [Arg("other", set)],
        "update" : [Arg("other", set)]
    })
    add_type(dict, [], {}, {
        "clear" : [],
        "copy" : [],
        "get" : [Arg("key"), Arg("default", value=Nothing())],
        "items" : [],
        "keys" : [],
        "values" : [],
        "pop" : [Arg("key")],
        "popitem" : [],
        "setdefault" : [Arg("key"), Arg("default")],
        "update" : [Arg("m", dict)]
    })

def add_basic_funcs():
    add_builtins(
        BuiltinFunc("len", [Arg("x")], len, type=int),
        BuiltinFunc("abs", [Arg("x")], abs),
        BuiltinFunc("pow", [Arg("base"), Arg("pow")], pow),
        BuiltinFunc("max", [Varg("vals")], max),
        BuiltinFunc("min", [Varg("vals")], min),
        BuiltinFunc("round", [Arg("x")], round),
        BuiltinFunc("all", [Varg("iters")], all, type=bool),
        BuiltinFunc("any", [Varg("iters")], any, type=bool),
        BuiltinFunc("sum", [Varg("elems")], sum),
        BuiltinFunc("hash", [Arg("obj")], hash, type=int),
        BuiltinFunc("id", [Arg("obj")], id, type=int),
        BuiltinFunc("sorted", [Arg("iter")], sorted),
        BuiltinFunc("reversed", [Arg("iter")], reversed),
        BuiltinFunc("slice", [Varg("args")], slice),
        BuiltinFunc("repr", [Arg("x")], repr),
        BuiltinFunc("hex", [Arg("x", int)], hex, type=str),
        BuiltinFunc("oct", [Arg("x", int)], oct, type=str),
        BuiltinFunc("bin", [Arg("x", int)], bin, type=str),
        BuiltinFunc("range", [Varg("args")], range, type=list),
        BuiltinFunc("enumerate", [Arg("iter")], enumerate, type=dict),
        BuiltinFunc("zip", [Arg("iter1"), Arg("iter2")], zip, type=dict)
    )

    # Math functions
    # TODO Add actual definitions for math functions
    add_builtins(*[BuiltinFunc(k, [Varg("args", type=(int, float))], v, (int, float)) for k, v in math.__dict__.items() if isinstance(v, Callable)])
