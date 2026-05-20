import type { NextPage, GetStaticProps } from "next";
import dynamic from "next/dynamic";
import type { ProductComponentType } from "src/types/shared";

import { MOCK_PRODUCTS } from "@Lib/mockData";

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
  // Frontend only: Use mock products
  const newArrivals = MOCK_PRODUCTS;
  const bestSellers = MOCK_PRODUCTS;

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
