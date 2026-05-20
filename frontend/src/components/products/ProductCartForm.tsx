import { ProductComponentType } from "src/types/shared";
import { useCurrencyFormatter } from "@Contexts/UIContext";

export default function ProductCartForm({
  product,
}: {
  product: ProductComponentType;
}) {
  const format = useCurrencyFormatter();

  return (
    <section className="product-cart-form" aria-label="Purchase information">
      <p className="product-cart-form__notice">
        Purchase and payment are completed on the external WordPress site. This
        storefront does not use an internal cart, checkout, payment, or account
        flow.
      </p>
      <p className="product-cart-form__price">
        Estimated price: {format((product.price - product.discount) * 1)}
      </p>
    </section>
  );
}
