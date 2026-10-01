from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from casestudies.models import CaseStudy
from products.models import Product
from solutions.models import Solution


class SolutionSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Solution.objects.published()


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Product.objects.published()


class CaseStudySitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.6

    def items(self):
        return CaseStudy.objects.published()

    def lastmod(self, obj):
        return obj.published_on


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ["home", "about", "solutions:list", "products:list", "casestudies:list", "contact:form"]

    def location(self, item):
        return reverse(item)
