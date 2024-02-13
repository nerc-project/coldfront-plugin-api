from django_scim.filters import UserFilterQuery
from django_scim.utils import get_user_model


class ColdfrontUserFilterQuery(UserFilterQuery):
    """
    Defines the SCIM filters for Coldfront users

    This class subclasses from `UserFilterQuery`, the class used by  `django-scim`
    to translate a SCIM filter query (i.e filter=uesrName eq foo) into a raw SQL query.

    For the translation to work, the query class needs to know which SCIM property maps
    to which SQL table column. This mapping must be defined with a `attr_map` dict
    (i.e with `("emails","value",None,): "email"` every SCIM filter query asking
    for emails.value will query the email field in the SQL database).

    The internals of UserFilterQuery is related to the `scim2-filter-parser` module.
    More explanation of `attr_map` is found
    [here](https://github.com/15five/scim2-filter-parser?tab=readme-ov-file#use)
    """

    model_getter = get_user_model
    attr_map = {
        # attr, sub attr, uri
        ("userName", None, None): "username",
        ("name", "familyName", None): "last_name",
        ("familyName", None, None): "last_name",
        ("name", "givenName", None): "first_name",
        ("givenName", None, None): "first_name",
        ("emails", "value", None): "email",
    }
