# dcargs

![build](https://github.com/brentyi/dcargs/workflows/build/badge.svg)
![mypy](https://github.com/brentyi/dcargs/workflows/mypy/badge.svg?branch=master)
![lint](https://github.com/brentyi/dcargs/workflows/lint/badge.svg)
[![codecov](https://codecov.io/gh/brentyi/dcargs/branch/master/graph/badge.svg)](https://codecov.io/gh/brentyi/dcargs)

<!-- vim-markdown-toc GFM -->

* [Overview](#overview)
* [Core interface](#core-interface)
* [Serialization](#serialization)
* [Feature list](#feature-list)
* [Alternative tools](#alternative-tools)

<!-- vim-markdown-toc -->

### Overview

**`dcargs`** is a library for defining argument parsers and configuration
objects using standard Python dataclasses.

```
pip install dcargs
```

Compared to other options, using dataclasses for configuration is:

- **Strongly typed.** Unlike dynamic configuration namespaces produced by
  libraries like `argparse`, `YACS`, `abseil`, or `ml_collections`, this means
  that IDE-assisted autocomplete, rename, refactor, go-to-definition operations
  work out-of-the-box, as do static checking tools like `mypy` and `pyright`.
- **Modular.** Most approaches to configuration objects require a centralized
  definition of all configurable fields. Hierarchically nesting dataclasses,
  however, makes it easy to distribute definitions, defaults, and documentation
  of configurable fields across modules or source files. A model configuration
  dataclass, for example, can be co-located in its entirety with the model
  implementation and dropped into any experiment configuration with an import —
  this eliminates redundancy and makes the entire module easy to port across
  codebases.
- **Noninvasive.** Dataclasses themselves are part of the standard Python
  library; defining them requires no external dependencies and they can be
  easily instantiated without `dcargs` (for example, within quick experiments in
  Jupyter notebooks).
- **Low effort.** Type annotations, docstrings, and default values for dataclass
  fields can be used to automatically generate argument parsers with informative
  helptext.

### Core interface

Our core interface is composed of a single function, which instantiates a
dataclass from an automatically generated CLI interface:

<table><tr><td>
<details>
    <summary>
    <code><strong>dcargs.parse</strong>(cls: Type[T], *, description:
    Optional[str], args: Optional[Sequence[str]], default_instance: Optional[T]) -> T</code>
    </summary>

<!-- prettier-ignore-start -->
<pre><code>Generate a CLI containing fields for a dataclass, and use it to create an
instance of the class. Gracefully handles nested dataclasses, container types,
generics, optional and default arguments, enums, and more.

Args:
    cls: Dataclass type to instantiate.

Keyword Args:
    description: Description text for the parser, displayed when the --help flag is
        passed in. If not specified, the dataclass docstring is used. Mirrors argument
        from `argparse.ArgumentParser()`.
    args: If set, parse arguments from a sequence of strings instead of the
        commandline. Mirrors argument from `argparse.ArgumentParser.parse_args()`.
    default_instance: An instance of `T` to use for default values. Helpful for overriding fields
        in an existing instance; if not specified, the field defaults are used instead.

Returns:
    Instantiated dataclass.</code></pre>
<!-- prettier-ignore-end -->

</details>
</td></tr></table>

**Example usage**

If you're familiar with dataclasses, writing a script with `dcargs.parse()` is
simple!

```python
# examples/simple.py
import dataclasses

import dcargs


@dataclasses.dataclass
class Args:
    field1: str  # A string field.
    field2: int  # A numeric field.
    flag: bool = False # A boolean flag.


if __name__ == "__main__":
    args = dcargs.parse(Args)
    print(args)
```

We can run this to get:

```
$ python simple.py --help
usage: simple.py [-h] --field1 STR --field2 INT [--flag]

required arguments:
  --field1 STR  A string field.
  --field2 INT  A numeric field.

optional arguments:
  -h, --help    show this help message and exit
  --flag        A boolean flag.
```

```
$ python simple.py --field1 string --field2 4
Args(field1='string', field2=4, flag=False)
```

Note that we also support significantly more complex structures and annotations,
including nested dataclasses, container types, generics, optional and default
arguments, enums, and more. Examples of additional features can be found in the
[examples](./examples/) and [unit tests](./tests/); a
[feature list](#feature-list) is also included below.

### Serialization

As a secondary feature, we also introduce two functions for human-readable
dataclass serialization:

- <code><strong>dcargs.from_yaml</strong>(cls: Type[T], stream: Union[str,
  IO[str], bytes, IO[bytes]]) -> T</code> and
  <code><strong>dcargs.to_yaml</strong>(instance: T) -> str</code> convert
  between YAML-style strings and dataclass instances.

The functions attempt to strike a balance between flexibility and robustness —
in contrast to naively dumping or loading dataclass instances (via pickle,
PyYAML, etc), explicit type references enable custom tags that are robust
against code reorganization and refactor, while a PyYAML backend enables
serialization of arbitrary Python objects.

Particularly for cases where serialized dataclasses need to exit the Python
ecosystem, [dacite](https://github.com/konradhalas/dacite) is also a good option
(at the cost of a little bit of flexibility).

### Feature list

The parse function supports a wide range of dataclass definitions, while
automatically generating helptext from comments/docstrings. A selection of
features are shown in the [examples](./examples/).

Our unit tests cover many more complex type annotations, including classes
containing:

- Types natively accepted by `argparse`: str, int, float, pathlib.Path, etc
- Default values for optional parameters
- Booleans, which are automatically converted to flags when provided a default
  value (eg `action="store_true"` or `action="store_false"`; in the latter case,
  we prefix names with `no-`)
- Enums (via `enum.Enum`; argparse's `choices` is populated and arguments are
  converted automatically)
- Various container types. Some examples:
  - `typing.ClassVar` types (omitted from parser)
  - `typing.Optional` types
  - `typing.Literal` types (populates argparse's `choices`)
  - `typing.Sequence` types (populates argparse's `nargs`)
  - `typing.List` types (populates argparse's `nargs`)
  - `typing.Tuple` types, such as `typing.Tuple[T1, T2, T3]` or
    `typing.Tuple[T, ...]` (populates argparse's `nargs`, and converts
    automatically)
  - `typing.Set` types (populates argparse's `nargs`, and converts
    automatically)
  - `typing.Final` types and `typing.Annotated` (for parsing, these are
    effectively no-ops)
  - Nested combinations of the above: `Optional[Literal[T]]`,
    `Final[Optional[Sequence[T]]]`, etc
- Nested dataclasses
  - Simple nesting (see `OptimizerConfig` in
    [./examples/nested.py](./examples/nested.py))
  - Unions over nested dataclasses (subparsers, see
    [./examples/subparsers.py](./examples/subparsers.py))
  - Optional unions over nested dataclasses (optional subparsers)
- Generic dataclasses (including nested generics, see
  [./examples/generics.py](./examples/generics.py))

Some other design decisions that we've put effort into:

- Strong typing: we actively avoid relying on strings or dynamic namespace
  objects (eg `argparse.Namespace`).
- Simplicity + strict abstractions: we're focused on a single function API, and
  don't leak any argparse implementation details to the user level. We also
  intentionally don't offer any way to add argument parsing-specific logic to
  dataclass definitions. (in contrast, some of the libaries above rely heavily
  on dataclass field metadata, or on the more extreme end inheritance+decorators
  to make parsing-specific dataclasses)
- Hyphens over underscores. For example, field names with underscores
  (`argument_name`) are parsed with hyphens (`--argument-name`).
  ([why?](https://stackoverflow.com/questions/1253679/should-command-line-options-in-posix-style-operating-systems-be-underscore-style))

### Alternative tools

The core functionality of `dcargs` --- generating an argument parser from type
annotations --- can be found as a subset of the features offered by many other
libraries. A summary of some distinguishing features:

|                                                                                                              | Choices from literals                                    | Generics | Docstrings as helptext | Nesting | Subparsers | Containers |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- | -------- | ---------------------- | ------- | ---------- | ---------- |
| **dcargs**                                                                                                   | ✓                                                        | ✓        | ✓                      | ✓       | ✓          | ✓          |
| **[datargs](https://github.com/roee30/datargs)**                                                             | ✓                                                        |          |                        |         | ✓          | ✓          |
| **[tap](https://github.com/swansonk14/typed-argument-parser)**                                               | ✓                                                        |          | ✓                      |         | ✓          | ✓          |
| **[simple-parsing](https://github.com/lebrice/SimpleParsing)**                                               | [soon](https://github.com/lebrice/SimpleParsing/pull/86) |          | ✓                      | ✓       | ✓          | ✓          |
| **[argparse-dataclass](https://pypi.org/project/argparse-dataclass/)**                                       |                                                          |          |                        |         |            |            |
| **[argparse-dataclasses](https://pypi.org/project/argparse-dataclasses/)**                                   |                                                          |          |                        |         |            |            |
| **[dataclass-cli](https://github.com/malte-soe/dataclass-cli)**                                              |                                                          |          |                        |         |            |            |
| **[clout](https://pypi.org/project/clout/)**                                                                 |                                                          |          |                        | ✓       |            |            |
| **[hf_argparser](https://github.com/huggingface/transformers/blob/master/src/transformers/hf_argparser.py)** |                                                          |          |                        |         |            | ✓          |
| **[pyrallis](https://github.com/eladrich/pyrallis/)**                                                        |                                                          |          | ✓                      | ✓       |            | ✓          |

Note that most of these other libraries offer other features that you might find
useful, such as `attrs` support (`datargs`, `clout`), registration for custom
types (`pyrallis`), different approaches for serialization and config files
(`tap`, `pyrallis`), simultaneous parsing of multiple dataclasses
(`simple-parsing`), etc.
