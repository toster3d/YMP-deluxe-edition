"""
This type stub file was generated by pyright.
"""

class Namespace(dict):
    def __getattr__(self, name):
        ...
    
    def __setattr__(self, name, value): # -> None:
        ...
    


_friendly_location = ...
text_type = ...
class Argument:
    """
    :param name: Either a name or a list of option strings, e.g. foo or
        -f, --foo.
    :param default: The value produced if the argument is absent from the
        request.
    :param dest: The name of the attribute to be added to the object
        returned by :meth:`~reqparse.RequestParser.parse_args()`.
    :param bool required: Whether or not the argument may be omitted (optionals
        only).
    :param action: The basic type of action to be taken when this argument
        is encountered in the request. Valid options are "store" and "append".
    :param ignore: Whether to ignore cases where the argument fails type
        conversion
    :param type: The type to which the request argument should be
        converted. If a type raises an exception, the message in the
        error will be returned in the response. Defaults to :class:`unicode`
        in python2 and :class:`str` in python3.
    :param location: The attributes of the :class:`flask.Request` object
        to source the arguments from (ex: headers, args, etc.), can be an
        iterator. The last item listed takes precedence in the result set.
    :param choices: A container of the allowable values for the argument.
    :param help: A brief description of the argument, returned in the
        response when the argument is invalid. May optionally contain
        an "{error_msg}" interpolation token, which will be replaced with
        the text of the error raised by the type converter.
    :param bool case_sensitive: Whether argument values in the request are
        case sensitive or not (this will convert all values to lowercase)
    :param bool store_missing: Whether the arguments default value should
        be stored if the argument is missing from the request.
    :param bool trim: If enabled, trims whitespace around the argument.
    :param bool nullable: If enabled, allows null value in argument.
    """
    def __init__(self, name, default=..., dest=..., required=..., ignore=..., type=..., location=..., choices=..., action=..., help=..., operators=..., case_sensitive=..., store_missing=..., trim=..., nullable=...) -> None:
        ...
    
    def __str__(self) -> str:
        ...
    
    def __repr__(self): # -> str:
        ...
    
    def source(self, request): # -> Any | dict[Any, Any] | MultiDict[Any, Any]:
        """Pulls values off the request in the provided location
        :param request: The flask request object to parse arguments from
        """
        ...
    
    def convert(self, value, op): # -> FileStorage | Decimal | None:
        ...
    
    def handle_validation_error(self, error, bundle_errors): # -> tuple[Any, dict[Any, Any | str]] | None:
        """Called when an error is raised while parsing. Aborts the request
        with a 400 status and an error message

        :param error: the error that was raised
        :param bundle_errors: do not abort when first error occurs, return a
            dict with the name of the argument and the error message to be
            bundled
        """
        ...
    
    def parse(self, request, bundle_errors=...):
        """Parses argument value(s) from the request, converting according to
        the argument's type.

        :param request: The flask request object to parse arguments from
        :param bundle_errors: Do not abort when first error occurs, return a
            dict with the name of the argument and the error message to be
            bundled
        """
        ...
    


class RequestParser:
    """Enables adding and parsing of multiple arguments in the context of a
    single request. Ex::

        from flask_restful import reqparse

        parser = reqparse.RequestParser()
        parser.add_argument('foo')
        parser.add_argument('int_bar', type=int)
        args = parser.parse_args()

    :param bool trim: If enabled, trims whitespace on all arguments in this
        parser
    :param bool bundle_errors: If enabled, do not abort when first error occurs,
        return a dict with the name of the argument and the error message to be
        bundled and return all validation errors
    """
    def __init__(self, argument_class=..., namespace_class=..., trim=..., bundle_errors=...) -> None:
        ...
    
    def add_argument(self, *args, **kwargs): # -> Self:
        """Adds an argument to be parsed.

        Accepts either a single instance of Argument or arguments to be passed
        into :class:`Argument`'s constructor.

        See :class:`Argument`'s constructor for documentation on the
        available options.
        """
        ...
    
    def parse_args(self, req=..., strict=..., http_error_code=...): # -> Namespace:
        """Parse all arguments from the provided request and return the results
        as a Namespace

        :param req: Can be used to overwrite request from Flask
        :param strict: if req includes args not in parser, throw 400 BadRequest exception
        :param http_error_code: use custom error code for `flask_restful.abort()`
        """
        ...
    
    def copy(self): # -> Self:
        """ Creates a copy of this RequestParser with the same set of arguments """
        ...
    
    def replace_argument(self, name, *args, **kwargs): # -> Self:
        """ Replace the argument matching the given name with a new version. """
        ...
    
    def remove_argument(self, name): # -> Self:
        """ Remove the argument matching the given name. """
        ...
    


