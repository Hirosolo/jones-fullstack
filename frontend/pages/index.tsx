import type { NextPage, GetStaticProps } from "next";
import dynamic from "next/dynamic";
import type { ProductComponentType } from "src/types/shared";

import { MOCK_PRODUCTS } from "@Lib/mockData";
import { fetchProducts } from "@Lib/api";

const CollectionSection = dynamic(
  () => import("@Components/home/CollectionSection")
);
const ProductsSection = dynamic(
  () => import("@Components/home/ProductsSection")
);
const GenderSection = dynamic(() => import("@Components/home/GenderSection"));

const Home: NextPage<HomePropTypes> = ({
  newArrivals,
  bestSellers,
  newArrivalsImgDataUrls,
  bestSellersImgDataUrls,
}) => {
  return (
    <>
      <CollectionSection />
      <ProductsSection
        productImageDataUrls={newArrivalsImgDataUrls}
        products={newArrivals}
        title="new arrivals"
        url="/category/new"
      />
      <GenderSection />
      <ProductsSection
        productImageDataUrls={bestSellersImgDataUrls}
        products={bestSellers}
        title="best sellers"
        url="/category/new?sort=best"
      />
    </>
  );
};

export const getStaticProps: GetStaticProps = async () => {
  // Try fetching from backend, fall back to mock products
  let newArrivals = MOCK_PRODUCTS;
  let bestSellers = MOCK_PRODUCTS;
  try {
    const products = await fetchProducts();
    newArrivals = products;
    bestSellers = products;
  } catch (e) {
    // keep mocks
  }

  // Placeholder for image data URLs if needed, otherwise empty
  const newArrivalsImgDataUrls: Record<string, string> = {};
  const bestSellersImgDataUrls: Record<string, string> = {};

  return {
    props: {
      newArrivals,
      bestSellers,
      newArrivalsImgDataUrls,
      bestSellersImgDataUrls,
    },
  };
};

export default Home;

interface HomePropTypes {
  newArrivals: ProductComponentType[];
  bestSellers: ProductComponentType[];
  newArrivalsImgDataUrls: Record<string, string>;
  bestSellersImgDataUrls: Record<string, string>;
}
