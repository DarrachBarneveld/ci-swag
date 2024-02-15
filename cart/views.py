"""Cart Views"""
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from products.models import Product

def view_cart(request):
    """ A view that renders the cart contents page """

    return render(request, 'cart/cart.html')



def add_to_cart(request, item_id):
    """ Add a quantity of the specified product to the shopping cart """

    quantity = request.POST.get('quantity')
    redirect_url = request.POST.get('redirect_url')

    product = get_object_or_404(Product, pk=item_id)

    print(product)

    cart = request.session.get('cart', {})

    if item_id in list(cart.keys()) and quantity:
        cart[item_id] += int(quantity)
    elif quantity:
        cart[item_id] = int(quantity)
    else:
        cart[item_id] = 1


    request.session['cart'] = cart
    return redirect(redirect_url)

def update_cart(request, item_id):
    """Adjust the quantity of the specified product to the specified amount"""

    quantity = int(request.POST.get('quantity'))
    redirect_url = request.POST.get('redirect_url')

    cart = request.session.get('cart', {})

    if quantity > 0:
        cart[item_id] = quantity
    else:
        cart.pop(item_id)

    request.session['cart'] = cart
    return redirect(redirect_url)


def remove_from_cart(request, item_id):
    """Remove the item from the shopping cart"""

    cart = request.session.get('cart', {})
    redirect_url = request.POST.get('redirect_url')

    try:
        cart.pop(item_id)
        request.session['cart'] = cart
        return redirect(redirect_url)

    except Exception as e:
        return HttpResponse(status=500)
