import type { ProductComponentType } from "src/types/shared";
import { useEffect, useState, useRef } from "react";
import { Router, useRouter } from "next/router";
import { GetStaticPaths, GetStaticProps } from "next";

import FilterAccordion from "@Components/products/filter/FilterAccordion";
import SEO from "@Components/common/SEO";
import Constraints from "@Components/products/constraints";
import FilterSortSection from "@Components/products/FilterSortSection";
import ProductsGrid from "@Components/products/ProductsGrid";

import { useDialog } from "@Contexts/UIContext";
import ProductsProvider, {
  filterStateType,
  useProductsState,
} from "@Contexts/ProductsContext";
import { MOCK_PRODUCTS } from "@Lib/mockData";
import { fetchProducts } from "@Lib/api";
import { categories } from "@Components/header/MenuLists";
import { ProductPlaceholderImg } from "src/constants";
import { getPathString } from "src/utils";

function CategoryPage({ categoryId }: { categoryId: string }) {
  const { products } = useProductsState();
  const count = products.length;

  const [filterActive, setFilterActive] = useState(false);
  const { currentDialog } = useDialog();

  useEffect(() => {
    const toggleScroll = () => {
      if (typeof window !== 'undefined' && innerWidth <= 992)
        document.body.style.overflow = filterActive ? "hidden" : "auto";
    };
    toggleScroll();
    Router.events.on("routeChangeComplete", toggleScroll);
    return () => Router.events.off("routeChangeComplete", toggleScroll);
  }, [filterActive, currentDialog]);

  useEffect(() => {
    if (typeof window !== 'undefined' && innerWidth > 992) setFilterActive(true);
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

export default function CategoryPageWithContext({
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

  useEffect(() => {
    // Set category filter based on the route param
    const preFilter: Partial<filterStateType> = {
      page: categoryId === "all" ? "" : categoryId,
      category: categoryId === "all" ? "" : categoryId,
    };
    ref.current?.updateFilterState?.(preFilter);
  }, [categoryId]);

  return (
    <ProductsProvider
      productImagePlaceholders={productImagePlaceholders}
      ref={ref}
      preFilter={{
        page: categoryId === "all" ? "" : categoryId,
        category: categoryId === "all" ? "" : categoryId,
      }}
      products={products}
    >
      <CategoryPage categoryId={categoryId} />
    </ProductsProvider>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const paths = ["all", ...categories].map((category) => ({
    params: { categoryId: [getPathString(category)] },
  }));

  return {
    paths,
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps = async function ({ params }) {
  const [categoryParam = "all"] = params?.categoryId as string[];
  
  // Fetch all products from API
  let allProducts = MOCK_PRODUCTS;
  try {
    allProducts = await fetchProducts();
  } catch (e) {
    // fallback to mocks
  }

  // Filter products by category if not "all"
  const filteredProducts = 
    categoryParam === "all"
      ? allProducts
      : allProducts.filter((product) => {
          const catName = categories.find((c) => getPathString(c) === categoryParam) || "";
          return (
            (product as any).category?.toLowerCase() === catName.toLowerCase() ||
            (product.title || "").toLowerCase().includes(catName.toLowerCase())
          );
        });

  const productImagePlaceholders = filteredProducts.reduce<Record<string, string>>((acc, product) => {
    acc[product.id] = ProductPlaceholderImg;
    return acc;
  }, {});

  return {
    props: {
      products: filteredProducts,
      categoryId: categoryParam,
      productImagePlaceholders,
    },
    revalidate: 3600, // Revalidate every hour
  };
};
