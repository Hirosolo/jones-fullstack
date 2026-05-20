import type { ProductComponentType } from "src/types/shared";
import { useEffect, useState, useRef } from "react";
import { Router, useRouter } from "next/router";
import { GetServerSideProps } from "next";

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
import { ProductPlaceholderImg } from "src/constants";

function ProductsPage() {
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
      <SEO title="Products" />
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

export default function ProductsPageWithContext({
  products,
  productImagePlaceholders,
}: {
  products: ProductComponentType[];
  productImagePlaceholders: Record<string, string>;
}) {
  const router = useRouter();
  const ref = useRef<{ updateFilterState: Function }>(null);

  useEffect(() => {
    // Set filter state based on query params
    const { category = "", brand = "", keyword = "" } = router.query;
    const preFilter: Partial<filterStateType> = {
      category: typeof category === "string" ? category : "",
      brand: typeof brand === "string" ? brand : "",
      keyword: typeof keyword === "string" ? keyword : "",
    };
    ref.current?.updateFilterState?.(preFilter);
  }, [router.query]);

  return (
    <ProductsProvider
      productImagePlaceholders={productImagePlaceholders}
      ref={ref}
      preFilter={{
        category: typeof router.query.category === "string" ? router.query.category : "",
        brand: typeof router.query.brand === "string" ? router.query.brand : "",
        keyword: typeof router.query.keyword === "string" ? router.query.keyword : "",
      }}
      products={products}
    >
      <ProductsPage />
    </ProductsProvider>
  );
}

export const getServerSideProps: GetServerSideProps = async function ({ query }) {
  // Fetch all products from API
  let allProducts = MOCK_PRODUCTS;
  try {
    allProducts = await fetchProducts();
  } catch (e) {
    // fallback to mocks
  }

  const productImagePlaceholders = allProducts.reduce<Record<string, string>>((acc, product) => {
    acc[product.id] = ProductPlaceholderImg;
    return acc;
  }, {});

  return {
    props: {
      products: allProducts,
      productImagePlaceholders,
    },
  };
};
