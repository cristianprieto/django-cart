from django.test import TestCase
from models import Cart, Item
from django.contrib.auth.models import User, AnonymousUser
import datetime
from decimal import Decimal
from django.http import HttpRequest

from cart import Cart as CartManager


class CartAndItemModelsTestCase(TestCase):

    def _create_cart_in_database(self, creation_date=datetime.datetime.now(),
            checked_out=False):
        """
            Helper function so I don't repeat myself
        """
        cart = Cart()
        cart.creation_date = creation_date
        cart.checked_out = False
        cart.save()
        return cart

    def _create_item_in_database(self, cart, product, quantity=1,
            unit_price=Decimal("100")):
        """
            Helper function so I don't repeat myself
        """
        item = Item()
        item.cart = cart
        item.product = product
        item.quantity = quantity
        item.unit_price = unit_price
        item.save()

        return item

    def _create_user_in_database(self):
        """
            Helper function so I don't repeat myself
        """
        user = User(username="user_for_sell", password="sold",
                email="example@example.com")
        user.save()
        return user

    def test_cart_creation(self):
        creation_date = datetime.datetime.now()
        cart = self._create_cart_in_database(creation_date)
        id = cart.id

        cart_from_database = Cart.objects.get(pk=id)
        self.assertEquals(cart, cart_from_database)

    def test_item_creation_and_association_with_cart(self):
        """
            This test is a little bit tricky since the Item tracks
            any model via django's content type framework. This was
            made in order to enable you to associate an item in the
            cart with your product model.

            As I wont make a product model here, I will assume my test
            store sells django users (django.contrib.auth.models.User)
            (lol) so I can test that this is working.

            So if you are reading this test to understand the API,
            you just need to change the user for your product model
            in your code and you're good to go.
        """
        user = self._create_user_in_database()

        cart = self._create_cart_in_database()
        item = self._create_item_in_database(cart, user, quantity=1, unit_price=Decimal("100"))

        # get the first item in the cart
        item_in_cart = cart.item_set.all()[0]
        self.assertEquals(item_in_cart, item,
                "First item in cart should be equal the item we created")
        self.assertEquals(item_in_cart.product, user,
                "Product associated with the first item in cart should equal the user we're selling")
        self.assertEquals(item_in_cart.unit_price, Decimal("100"),
                "Unit price of the first item stored in the cart should equal 100")
        self.assertEquals(item_in_cart.quantity, 1,
                "The first item in cart should have 1 in it's quantity")

    def test_total_item_price(self):
        """
        Since the unit price is a Decimal field, prefer to associate
        unit prices instantiating the Decimal class in
        decimal.Decimal.
        """
        user = self._create_user_in_database()
        cart = self._create_cart_in_database()

        # not safe to do as the field is Decimal type. It works for integers but
        # doesn't work for float
        item_with_unit_price_as_integer = self._create_item_in_database(cart, product=user, quantity=3, unit_price=100)

        self.assertEquals(item_with_unit_price_as_integer.total_price, 300)

        # this is the right way to associate unit prices
        item_with_unit_price_as_decimal = self._create_item_in_database(cart,
                product=user, quantity=4, unit_price=Decimal("3.20"))
        self.assertEquals(item_with_unit_price_as_decimal.total_price, Decimal("12.80"))

    def test_item_unicode(self):
        user = self._create_user_in_database()
        cart = self._create_cart_in_database()

        item = self._create_item_in_database(cart, product=user, quantity=3, unit_price=Decimal("100"))

        self.assertEquals(item.__unicode__(), "%s units of User %s" % (3, user.id))

    def test_cart_is_empty(self):
        cart = self._create_cart_in_database()

        self.assertEquals(cart.is_empty(), True)

    def test_cart_is_really_empty(self):
        user = self._create_user_in_database()
        cart = self._create_cart_in_database()

        self._create_item_in_database(cart, product=user, quantity=2, unit_price=Decimal("100"))
        self._create_item_in_database(cart, product=user, quantity=1, unit_price=Decimal("90"))

        self.assertEquals(cart.is_empty(), False)

    def test_cart_total_price(self):
        user = self._create_user_in_database()
        cart = self._create_cart_in_database()

        self._create_item_in_database(cart, product=user, quantity=1, unit_price=Decimal("100"))
        self._create_item_in_database(cart, product=user, quantity=2, unit_price=Decimal("150"))

        self.assertEquals(cart.total_price(), 400)


class CartManagerTestCase(TestCase):
    # Let's re-use some functions from the Model Test :)
    def _create_cart_in_request(self, creation_date=datetime.datetime.now(),
            checked_out=False):
        """
            Helper function so I don't repeat myself
        """
        r = HttpRequest()
        r.session = {}
        r.user = AnonymousUser()
        cart = CartManager(r)
        return cart

    def _create_item_in_database(self, cart, product, quantity=1,
            unit_price=Decimal("100")):
        """
            Helper function so I don't repeat myself
        """
        item = Item()
        item.cart = cart
        item.product = product
        item.quantity = quantity
        item.unit_price = unit_price
        item.save()

        return item

    def _create_user_in_database(self):
        """
            Helper function so I don't repeat myself
        """
        user = User(username="user_for_sell", password="sold",
                email="example@example.com")
        user.save()
        return user

    def test_cart_in_request(self):
        cart = self._create_cart_in_request()
        self.assertEquals(cart.cart.id, 1)

    def test_cart_user_is_anonymous(self):
        cart = self._create_cart_in_request()
        self.assertEquals(cart.cart.user, None)

    def test_cart_merge_user_anonuser(self):
        # anonymous user
        cart = self._create_cart_in_request()
        # registered user
        user = self._create_user_in_database()
        # let's create an item
        item = self._create_item_in_database(cart.cart, product=user, quantity=3, unit_price=100)
        # let's merge with the user that we created on the db
        cart = cart.merge(cart.cart.id, user)
        self.assertEquals(cart.id, 1)
        self.assertEquals(cart.user, user)

    def test_cart_clear(self):
        cart = self._create_cart_in_request()
        user = self._create_user_in_database()
        item = self._create_item_in_database(cart.cart, product=user, quantity=3, unit_price=100)
        self.assertEquals(cart.cart.is_empty(), False)
        cart.clear()
        self.assertEquals(cart.cart.is_empty(), True)


