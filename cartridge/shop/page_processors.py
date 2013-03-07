from functools import partial
from types import MethodType
from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import slugify

from mezzanine.conf import settings
from mezzanine.pages.page_processors import processor_for
from mezzanine.utils.views import paginate

from cartridge.shop.models import Category, Product

category_models = dict()


@processor_for(Category)
def category_processor(request, page):
    """
    Add paging/sorting to the products for the category.
    """

    product_model, category_model = category_models.get(
        page.category.product_model,
        (Product, Category))

    if category_model is not Category:
        page.category = category_model.objects.get(pk=page.category.pk)

        from mezzanine.pages import page_processors
        category_model_name = category_model._meta.object_name.lower()
        processors = page_processors.processors[category_model_name]
        return page_processors.run_page_processors(processors, request, page)

    settings.use_editable()
    products = product_model.objects.published(for_user=request.user)
    products.filter(page.category.filters()).distinct()
    sort_options = [(slugify(option[0]), option[1])
                    for option in settings.SHOP_PRODUCT_SORT_OPTIONS]
    sort_by = request.GET.get("sort", sort_options[0][1])
    products = paginate(products.order_by(sort_by),
                        request.GET.get("page", 1),
                        settings.SHOP_PER_PAGE_CATEGORY,
                        settings.MAX_PAGING_LINKS)
    products.sort_by = sort_by
    sub_categories = page.category.children.published()
    child_categories = Category.objects.filter(id__in=sub_categories)
    return {"products": products, "child_categories": child_categories}


def product_category(cls):

    if not (cls.__bases__[0] is Category and getattr(cls._meta, 'proxy', False)):
        raise ImproperlyConfigured("Product category must be a proxy of cartridge.shop.models.Category.")

    if not hasattr(cls, 'product_model'):
        raise ImproperlyConfigured("Product category must define the product_model attribute.")

    product_model = cls.product_model

    from cartridge.shop.page_processors import category_models
    model_name = product_model._meta.object_name.lower()
    if model_name in category_models:
        raise ImproperlyConfigured("Only one category can be registered per product.")
    cls.__init__ = MethodType(
        partial(cls.__init__, product_model=model_name),
        None,
        cls)
    category_models[model_name] = (product_model, cls)
    return cls