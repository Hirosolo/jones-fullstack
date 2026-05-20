import type { ProductComponentType } from "src/types/shared";
import { NextPage, GetStaticProps, GetStaticPaths } from "next";
import SEO from "@Components/common/SEO";
import { useCurrencyFormatter } from "@Contexts/UIContext";
import { MOCK_PRODUCTS } from "@Lib/mockData";
import { fetchProductBySlug, fetchProductSlugs, fetchProducts } from "@Lib/api";
import { getPathString } from "src/utils";
import { ProductPlaceholderImg } from "src/constants";
import ProductsGrid from "@Components/products/ProductsGrid";
import ShareButton from "@Components/common/ShareButton";
import ProductGallery from "@Components/products/ProductGallery";
import ProductCartForm from "@Components/products/ProductCartForm";
import ProductDetails from "@Components/products/ProductDetails";
import RatingStars from "@Components/common/RatingStars";

const ProductPage: NextPage<ProductPageType> = ({
  product,
  relatedProducts,
  imageDimensions,
  blurDataUrls,
}) => {
  const format = useCurrencyFormatter();
  
  if (!product) {
    return <div>Product not found</div>;
  }

  const {
    id,
    title,
    gender,
    price,
    discount,
    sku,
    year,
    color,
    salesCount,
    type,
    ratings,
  } = product;

  const cartPrice = (price - discount) * 1;
  const percentageOff = discount
    ? `${Math.floor((discount / price) * 100)}% off`
    : "";

  return (
    <>
      <SEO title={product.title} />

      <div className="product-view">
        <ProductGallery
          key={`gallery-${id}`}
          product={product}
          images={product.mediaURLs}
          dimensions={imageDimensions}
          blurDataUrls={blurDataUrls}
        />

        <div className="product-view__cart">
          <p className="product-view__gender">{gender}</p>
          <h1 className="product-view__name">{title}</h1>
          <RatingStars count={ratings} />

          <div className="product-view__details">
            <p className="product-view__details-info">
              <strong>Model No.:</strong> {sku.toUpperCase()}
            </p>
            <p className="product-view__details-info">
              <strong>Release Year:</strong> {year}
            </p>
            <p className="product-view__details-info">
              <strong>Upper:</strong> {type.toLocaleLowerCase()} Cut
            </p>
            <p className="product-view__details-info">
              <strong>Colorway:</strong> {color}
            </p>
          </div>

          <p className="product-view__price">
            {format(cartPrice)} <span>{percentageOff}</span>
          </p>

          <p className="product-view__sold">
            {salesCount ?? 0} Sold / Available
          </p>

          <ProductCartForm key={product.id} product={product} />
          <p className="product-view__shipping-info">Shipping is calculated at checkout.</p>

          <ShareButton
            title={product.title}
            description={product.details}
            image={product.mediaURLs[0]}
            hashtags="#jonesstore"
          />
        </div>

        <ProductDetails product={product} />
      </div>

      <div className="related-products">
        {relatedProducts.length ? (
          <>
            <h2 className="related-products__heading">Related <wbr/>Products</h2>
            <ProductsGrid products={relatedProducts} />
          </>
        ) : null}
      </div>
    </>
  );
};

export const getStaticPaths: GetStaticPaths = async () => {
  try {
    const slugs = await fetchProductSlugs();
    const paths = slugs.map((s) => ({ params: { productSlug: s } }));
    return { paths, fallback: false };
  } catch (e) {
    const paths = MOCK_PRODUCTS.map((product) => ({
      params: { productSlug: getPathString(`${product.title} ${product.sku}`) },
    }));
    return { paths, fallback: false };
  }
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const productSlug = params?.productSlug as string;
  // Try backend first
  try {
    const product = await fetchProductBySlug(productSlug);
    if (!product) return { notFound: true };

    const products = await fetchProducts().catch(() => []);

    const blurDataUrls = product.mediaURLs.reduce<Record<string, string>>((acc, url) => {
      acc[url] = ProductPlaceholderImg;
      return acc;
    }, {});

    const imageDimensions = product.mediaURLs.map(() => ({ width: 1000, height: 1000 }));

    return {
      props: {
        product,
        relatedProducts: products.filter((p) => p.id !== product.id),
        imageDimensions,
        blurDataUrls,
      },
    };
  } catch (e) {
    // Fallback to mocks
    const product = MOCK_PRODUCTS.find(
      (p) => getPathString(`${p.title} ${p.sku}`) === productSlug
    );
    if (!product) return { notFound: true };

    const blurDataUrls = product.mediaURLs.reduce<Record<string, string>>((acc, url) => {
      acc[url] = ProductPlaceholderImg;
      return acc;
    }, {});

    const imageDimensions = product.mediaURLs.map(() => ({ width: 1000, height: 1000 }));

    return {
      props: {
        product,
        relatedProducts: MOCK_PRODUCTS.filter((p) => p.id !== product.id),
        imageDimensions,
        blurDataUrls,
      },
    };
  }
};

export default ProductPage;

interface ProductPageType {
  product: ProductComponentType;
  relatedProducts: ProductComponentType[];
  imageDimensions: { width: number; height: number }[];
  blurDataUrls: Record<string, string>;
}
