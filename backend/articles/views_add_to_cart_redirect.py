import requests
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Hỗ trợ POST từ client Next.js hoặc form
@method_decorator(csrf_exempt, name='dispatch')
class AddToCartRedirectView(View):
    def post(self, request):
        sku = request.POST.get('sku')
        quantity = request.POST.get('quantity', 1)
        selected_color = request.POST.get('color')
        selected_size = request.POST.get('size')
        note = request.POST.get('note')

        try:
            # 1. Lấy product theo SKU
            r = requests.get(f'https://jones.com/wp-json/wc/v3/products?sku={sku}')
            r.raise_for_status()
            data = r.json()
            if not data:
                return HttpResponse('Không tìm thấy sản phẩm trên hệ thống thanh toán.', status=404)
            product = data[0]
            product_id = product['id']
            id_to_add = product_id
            # 2. Nếu là variable, lấy đúng variation
            if product.get('type') == 'variable':
                vres = requests.get(f'https://jones.com/wp-json/wc/v3/products/{product_id}/variations')
                vres.raise_for_status()
                variations = vres.json()
                found = None
                for v in variations:
                    match = True
                    if selected_color:
                        match = match and any(attr['name'].lower() == 'color' and attr['option'] == selected_color for attr in v['attributes'])
                    if selected_size:
                        match = match and any(attr['name'].lower() == 'size' and attr['option'] == selected_size for attr in v['attributes'])
                    if match:
                        found = v
                        break
                if found:
                    id_to_add = found['id']
                else:
                    return HttpResponse('Không tìm thấy biến thể sản phẩm phù hợp.', status=404)
            # 3. Redirect
            params = f'?add-to-cart={id_to_add}&quantity={quantity}'
            if note:
                params += f'&note={note}'
            redirect_url = f'https://jones.com/{params}'
            return HttpResponseRedirect(redirect_url)
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=500)
