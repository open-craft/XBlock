"""
Core classes for the XBlock family.

This code is in the Runtime layer, because it is authored once by edX
and used by all runtimes.

"""
import pkg_resources
import warnings

from xblock.exceptions import DisallowedFileError
from xblock.fields import String, List, Scope
import xblock.mixins
from xblock.mixins import (
    ScopedStorageMixin,
    HierarchyMixin,
    RuntimeServicesMixin,
    HandlersMixin,
    XmlSerializationMixin
)
from xblock.plugin import Plugin
from xblock.validation import Validation

# exposing XML_NAMESPACES as a member of core, in order to avoid importing mixins where
# XML_NAMESPACES are needed (e.g. runtime.py).
XML_NAMESPACES = xblock.mixins.XML_NAMESPACES

# __all__ controls what classes end up in the docs.
__all__ = ['XBlock']
UNSET = object()


class XBlockMixin(ScopedStorageMixin):
    """
    Base class for XBlock Mixin classes.

    XBlockMixin classes can add new fields and new properties to all XBlocks
    created by a particular runtime.

    """
    pass


class TagCombiningMetaclass(type):
    """
    Collects and combines `._class_tags` from all base classes and
    puts them together in one `.class_tags` attribute.
    """
    def __new__(mcs, name, bases, attrs):
        # Allow this method to access the `_class_tags`
        # pylint: disable=W0212
        class_tags = set([])
        # Collect the tags from all base classes.
        for base in bases:
            try:
                class_tags.update(base._class_tags)
            except AttributeError:
                # Base classes may have no ._class_tags, that's ok.
                pass
        attrs['_class_tags'] = class_tags
        return super(TagCombiningMetaclass, mcs).__new__(mcs, name, bases, attrs)


class XBlockMetaclass(
        HierarchyMixin.__metaclass__,
        ScopedStorageMixin.__metaclass__,
        RuntimeServicesMixin.__metaclass__,
        TagCombiningMetaclass,
):
    """
    Metaclass for XBlock.

    Combines all the metaclasses XBlocks needs:

    * `ChildrenModelMetaclass`
    * `ModelMetaclass`
    * `TagCombiningMetaclass`
    * `ServiceRequestedMetaclass`

    """
    pass


# -- Base Block
class XBlock(XmlSerializationMixin, HierarchyMixin, ScopedStorageMixin, RuntimeServicesMixin, HandlersMixin, Plugin):
    """Base class for XBlocks.

    Derive from this class to create a new kind of XBlock.  There are no
    required methods, but you will probably need at least one view.

    Don't provide the ``__init__`` method when deriving from this class.

    """

    __metaclass__ = XBlockMetaclass

    entry_point = 'xblock.v1'

    name = String(help="Short name for the block", scope=Scope.settings)
    tags = List(help="Tags for this block", scope=Scope.settings)

    _class_tags = set()

    @staticmethod
    def tag(tags):
        """Returns a function that adds the words in `tags` as class tags to this class."""
        def dec(cls):
            """Add the words in `tags` as class tags to this class."""
            # Add in this class's tags
            cls._class_tags.update(tags.replace(",", " ").split())  # pylint: disable=protected-access
            return cls
        return dec

    @classmethod
    def load_tagged_classes(cls, tag):
        """Produce a sequence of all XBlock classes tagged with `tag`."""
        # Allow this method to access the `_class_tags`
        # pylint: disable=W0212
        for name, class_ in cls.load_classes():
            if tag in class_._class_tags:
                yield name, class_

    @classmethod
    def open_local_resource(cls, uri):
        """Open a local resource.

        The container calls this method when it receives a request for a
        resource on a URL which was generated by Runtime.local_resource_url().
        It will pass the URI from the original call to local_resource_url()
        back to this method. The XBlock must parse this URI and return an open
        file-like object for the resource.

        For security reasons, the default implementation will return only a
        very restricted set of file types, which must be located in a folder
        called "public". XBlock authors who want to override this behavior will
        need to take care to ensure that the method only serves legitimate
        public resources. At the least, the URI should be matched against a
        whitelist regex to ensure that you do not serve an unauthorized
        resource.

        """
        # Verify the URI is in whitelisted form before opening for serving.
        # URI must begin with public/, and no file path component can start
        # with a dot, which prevents ".." and ".hidden" files.
        if not uri.startswith("public/"):
            raise DisallowedFileError("Only files from public/ are allowed: %r" % uri)
        if "/." in uri:
            raise DisallowedFileError("Only safe file names are allowed: %r" % uri)
        return pkg_resources.resource_stream(cls.__module__, uri)

    def __init__(self, runtime, field_data=None, scope_ids=UNSET):
        """
        Construct a new XBlock.

        This class should only be instantiated by runtimes.

        Arguments:

            runtime (:class:`.Runtime`): Use it to access the environment.
                It is available in XBlock code as ``self.runtime``.

            field_data (:class:`.FieldData`): Interface used by the XBlock
                fields to access their data from wherever it is persisted.
                Deprecated.

            scope_ids (:class:`.ScopeIds`): Identifiers needed to resolve
                scopes.

        """
        if scope_ids is UNSET:
            raise TypeError('scope_ids are required')

        # Provide backwards compatibility for external access through _field_data
        super(XBlock, self).__init__(runtime=runtime, scope_ids=scope_ids, field_data=field_data)

    def render(self, view, context=None):
        """Render `view` with this block's runtime and the supplied `context`"""
        return self.runtime.render(self, view, context)

    def validate(self):
        """
        Ask this xblock to validate itself. Subclasses are expected to override this
        method, as there is currently only a no-op implementation.
        """
        return Validation(self.scope_ids.usage_id)

# Maintain backwards compatibility
import xblock.exceptions


class KeyValueMultiSaveError(xblock.exceptions.KeyValueMultiSaveError):
    """
    Backwards compatibility class wrapper around :class:`.KeyValueMultiSaveError`.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn("Please use xblock.exceptions.KeyValueMultiSaveError", DeprecationWarning, stacklevel=2)
        super(KeyValueMultiSaveError, self).__init__(*args, **kwargs)


class XBlockSaveError(xblock.exceptions.XBlockSaveError):
    """
    Backwards compatibility class wrapper around :class:`.XBlockSaveError`.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn("Please use xblock.exceptions.XBlockSaveError", DeprecationWarning, stacklevel=2)
        super(XBlockSaveError, self).__init__(*args, **kwargs)
