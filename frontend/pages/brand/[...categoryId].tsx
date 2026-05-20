import type { ProductComponentType } from "src/types/shared";
import { useEffect, useState, useRef } from "react";
import { Router, useRouter } from "next/router";
import { Gender } from "src/types/shared";
import { GetStaticPaths, GetStaticProps } from "next";

import FilterAccordion from "@Components/products/filter/FilterAccordion";
import SEO from "@Components/common/SEO";
import Constraints from "@Components/products/constraints";
import FilterSortSection from "@Components/products/FilterSortSection";
import ProductsGrid from "@Components/products/ProductsGrid";

import { HIGHEST_PRICE } from "src/constants";
import { useDialog } from "@Contexts/UIContext";
import ProductsProvider, {
  filterStateType,
  useProductsState,
} from "@Contexts/ProductsContext";
import { MOCK_PRODUCTS } from "@Lib/mockData";
import { brandsData } from "@Components/header/MenuLists";
import { ProductPlaceholderImg } from "src/constants";
import { getPathString } from "src/utils";

function BrandPage({ categoryId }: { categoryId: string }) {
  const { products } = useProductsState();
  const count = products.length;

  const [filterActive, setFilterActive] = useState(false);
  const { currentDialog } = useDialog();

  useEffect(() => {
    const toggleScroll = () => {
      if (typeof window !== "undefined" && innerWidth <= 992)
        document.body.style.overflow = filterActive ? "hidden" : "auto";
    };
    toggleScroll();
    Router.events.on("routeChangeComplete", toggleScroll);
    return () => Router.events.off("routeChangeComplete", toggleScroll);
  }, [filterActive, currentDialog]);

  useEffect(() => {
    if (typeof window !== "undefined" && innerWidth > 992) setFilterActive(true);
  }, []);

  return (
    <>
      <SEO title={categoryId} />
      <Constraints allProductsCount={count} currentProductsCount={count} />
      <FilterSortSection toggleFilter={() => setFilterActive(!filterActive)} />

      <div className="results">
        <FilterAccordion
          active={filterActive}
          setState={() => setFilterActive(false)}
        />

        <div
          className={
            "results__container" +
            (filterActive ? " results__container--filter" : "")
          }
        >
          <ProductsGrid products={products} />
        </div>
      </div>
    </>
  );
}

export default function BrandPageWithContext({
  categoryId,
  products,
  productImagePlaceholders,
}: {
  categoryId: string;
  products: ProductComponentType[];
  productImagePlaceholders: Record<string, string>;
}) {
  const router = useRouter();
  const ref = useRef<{ updateFilterState: Function }>(null);

  const getQueryAsFilter = () => {
    const queryAsFilter: Partial<filterStateType> = {
      price: [0, HIGHEST_PRICE],
    };

    Object.keys(router.query).forEach((param) => {
      const value = router.query[param];
      if (
        param == "categoryId" &&
        value &&
        value[0] &&
        Gender[value[0].toUpperCase() as keyof typeof Gender]
      ) {
        queryAsFilter["gender"] = value[0].toUpperCase() as Gender;
        if (value[1]) queryAsFilter["search"] = value[1];
      } else if (
        param == "categoryId" &&
        (value == "colorways" || value == "new")
      ) {
        queryAsFilter["page"] = value;
      }
      if (param == "size" || param == "year") {
        queryAsFilter[param] = Array.isArray(value)
          ? value.map((v) => Number(v))
          : [Number(value)];
      }
      if (param == "min_price" && queryAsFilter["price"]) {
        queryAsFilter["price"][0] = Number(value);
      }
      if (param == "max_price" && queryAsFilter["price"]) {
        queryAsFilter["price"][1] = Number(value);
      }
      if (param == "color" || param == "height") {
        queryAsFilter[param] = Array.isArray(value) ? value : [value ?? ""];
      }
      if (param == "sort" && typeof value == "string") {
        queryAsFilter[param] = value;
      }
    });
    return queryAsFilter;
  };

  useEffect(() => {
    ref.current?.updateFilterState?.(getQueryAsFilter());
  });

  return (
    <ProductsProvider
      productImagePlaceholders={productImagePlaceholders}
      ref={ref}
      preFilter={getQueryAsFilter()}
      products={products}
    >
      <BrandPage categoryId={categoryId} />
    </ProductsProvider>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const paths = [
    ...Object.keys(brandsData),
    ...Object.values(brandsData).flat(),
  ].map((categoryId) => ({
    params: { categoryId: [getPathString(categoryId)] },
  }));

  return {
    paths,
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps = async function ({ params }) {
  const [category = "all"] = params?.categoryId as string[];

  // Frontend only: Use mock products
  const allProducts = MOCK_PRODUCTS;
  const productImagePlaceholders = allProducts.reduce<Record<string, string>>(
    (acc, product) => {
      acc[product.id] = ProductPlaceholderImg;
      return acc;
    },
    {}
  );

  return {
    props: {
      products: allProducts,
      count: allProducts.length,
      categoryId: category ?? "",
      productImagePlaceholders,
    },
  };
};