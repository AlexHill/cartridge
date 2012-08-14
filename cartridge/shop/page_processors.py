
from django.template.defaultfilters import slugify

from mezzanine.conf import settings
from mezzanine.pages import page_processors
from mezzanine.pages.page_processors import processors, processor_for
from mezzanine.utils.views import paginate

from cartridge.shop.models import Category, Product


@processor_for(Category)
def category_processor(request, page):
    """
    Add paging/sorting to the products for the category.
    """

    if page.category.product_model:
        proxy_model = page.category.product_model + "category";
        if proxy_model in processors:
            context = {}
            for processor, exact_page in processors[proxy_model]:
                if page.is_current or not exact_page:
                    context.update(processor(request, page))
            return context

    settings.use_editable()
    products = Product.objects.published(for_user=request.user
                                ).filter(page.category.filters()).distinct()
    sort_options = [(slugify(option[0]), option[1])
                    for option in settings.SHOP_PRODUCT_SORT_OPTIONS]
    sort_by = request.GET.get("sort", sort_options[0][1])
    products = paginate(products.order_by(sort_by),
                        request.GET.get("page", 1),
                        settings.SHOP_PER_PAGE_CATEGORY,
                        settings.MAX_PAGING_LINKS)
    products.sort_by = sort_by
    return {"products": products}
