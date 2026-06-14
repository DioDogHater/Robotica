# Robotica, a mod-oriented scripting language for Python
The robotica language is a simple and python-like language with
type checking and a flexible syntax. Its purpose is to provide a
general interface for mods and user generated scripts, with limited
access to sensitive functionality, without having to write a whole
port of your game's code in Robotica.
<br></br>

## Requirements
- Python 3.13 or later

## Current Features
- AST (Abstract Syntax Tree) generation
- Code execution from a global scope (that can return a value)
- All Python basic operations (works with magic methods as well)
- Functions (and nested functions)
- If, elif and else statements
- while and for loops
- Lists and dictionaries
- Custom types and type checking

## Easy to use
The Robotica language is very easy to implement in your game or application.

For instance, adding variables to a Robotica script's global scope is as easy
as calling a method with a newly created `Var` object:

`global_scope.add_var(Var("my_var", value=10.252, type=float))`
<br></br>

In fact, you can even add python functions and types in Robotica with a few lines
of code:
```python
import extern as rbt

rbt.add_builtins(
    rbt.Builtin("print", [rbt.Varg("args")], print),
    rbt.Builtin("input", [rbt.Arg("prompt", str)], input),
    # Multiple types such as int | float are represented using tuples
    rbt.Builtin("test", [rbt.Arg("test_arg1", (int, float))], test_func)
)
```
*NOTE: to add carefully selected basic python functions, call `add_basic_funcs()` from `extern.py`.*
<br></br>

Now, let's add this `Enemy` type with these properties and methods to Robotica:
```
class Enemy {
    + position : Vector3
    + rotation : float
    + (read-only) target : Player
    + (read-only) health : int
    
    + Enemy(position : Vector2, target : Player)
    + set_target(target : Any)
    + take_damage(damage : int)
}
```

The function `add_type` in `extern.py` lets you define a Python type.
It takes in your type, the arguments to the constructor of your type
(*if it can be built from Robotica*),
then its properties and methods. Each argument is represented with a `Arg` object.
Additional arguments (*aka variable arguments*) are represented with a `Varg` object.
A type's methods should be a dictionary of each accessible method's name and their arguments,
in a list.
```python
import extern as rbt

rbt.add_type(
    Enemy,
    [rbt.Arg("position", Vector2), rbt.Arg("target", Player)],
    {"position", "rotation", "target", "health"},
    {
        "set_target" : [rbt.Arg("target", None)]   # Any is represented as None
        "take_damage" : [rbt.Arg("damage", int)]
    }
)
```
*NOTE: type checking of attributes should be done in Python for added types.*

## Syntax
#### Basic types
- `any` : value of any type
- `nothing`, `none` : no value
- `bool` : boolean value (`true` or `false`)
- `int` : whole numbers
- `float` : fractional numbers
- `str` : text
- `list` : list of any length, containing values
- `set` : contains specific values
- `dict` : dictionary, containing keys and values attached to them

**nothing is compatible with any type.**

*NOTE: you must call `add_basic_types()` from `extern.py` to use most of these.*
<br></br>

#### Constants
`nothing`, `none` = `None`

`true`, `yes` = `True`

`false`, `no` = `False`
<br></br>

#### Code blocks
They are a bundle of statements that are used in functions, ifs, loops, etc.

A code block in Python begins with `:` and must be indented (spaces must be
added). However, in Robotica, code blocks can also be enclosed by braces `{}`,
like in C++, Java, Javascript, etc.

#### Scope
A scope is a block of code that has its own functions and variables that are
local to itself. What that signifies is that a variable / function created in
a scope can only be accessed inside that scope. However, functions and variables
created outside the scope can be accessed. Currently, there are only 2 types of
scopes:
1. The global scope &rarr; contains all of the code of the script
2. A function scope &rarr; the code inside a function (see *Functions*)
<br></br>

#### Variables
A variable must be created before using it.
Its type is optional and if no initial value is provided, it will have a value
of `nothing`, the equivalent of `None` in Python.

If a variable with the same name has already been created in the same scope,
the new variable will overwrite the old one. However, if a variable outside
the scope has the same name, the new local variable will take its place only
inside the current scope.

`var my_var : type = value`
<br></br>

#### Functions
A function has a name, arguments, a return type and a body. The function body
is a scope, that can contain other functions.

Arguments can optionally have a type and a default value.
If an argument has a default value, following arguments must also have a default value.

Variable arguments are always at the end of a function's arguments and are the
extra arguments given when the functionis called.
Variable arguments are a list of all extra arguments and they can be
empty, if there are no extra arguments.

Defining functions is similar to python, except `def` can be replaced by `fn` or `func`.

Additionally, variable arguments are defined using `...`, not `*`.

```
def my_func(arg1 : type, arg2 : type = value, ...args : type) -> type:
    # Code inside
```
*NOTE: if your function is empty, you should use `{}` as the function's code block.*
<br></br>

#### If / elif / else
If, elif and else do not create their own scope, like in Python.

Elif and else statements can only be used after an if / elif.

`elif` can be replaced for `else if` for aesthetics.

```
if condition:
    # Code if condition is true
elif condition:
    # Code if first condition is false
    # and second condition is true
elif condition:
    # Code if ...
else:
    # Code if all conditions were false
```
<br></br>

#### While
The while loop will repeat as long as its condition is true.

You can use the `break` statement to stop the loop and the
`continue` statement to skip to the next repeat of the loop.

```
while condition:
    # Code to repeat
```
<br></br>

#### Iterator for loop : the Python  `for`
```
for x in iterator:
    # Code to repeat

for x, y in iterator:
    # Code to repeat
```
<br></br>
#### Stepping for loop : the Python  `for i in range(...)`
```
for i = start to end:
    # Code to repeat

for i = start to end, +1:
    # Code to repeat

for i from start to end step +1:
    # Code to repeat
```
