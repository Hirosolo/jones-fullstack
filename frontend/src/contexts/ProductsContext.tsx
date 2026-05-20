import type { ProductComponentType } from "src/types/shared";

import {
  createContext,
  ReactNode,
  useContext,
  useState,
  useRef,
  useImperativeHandle,
  forwardRef,
  ForwardedRef,
} from "react";

import { HIGHEST_PRICE } from "src/constants";
import { compareObjects } from "src/utils";
import Router from "next/router";

export interface filterStateType {
  keyword?: string;
  category?: string;
  brand?: string;
  sort?: string;
  page: string;
}
export type filterStateKeys = keyof filterStateType;

const _filterState: filterStateType = {
  page: "",
  keyword: "",
  category: "",
  brand: "",
};

interface ProductStateType {
  products: ProductComponentType[];
  filterState: filterStateType;
  sortBy: string;
  productImagePlaceholders: Record<string, string>;
  filterListings: (action: { [type: string]: unknown }) => void;
  sortListings: (sortBy: string) => void;
  clearFilters: () => void;
}

const ProductsState: ProductStateType = {
  products: [],
  filterState: _filterState,
  sortBy: "",
  productImagePlaceholders: {},
  filterListings: () => null,
  sortListings: () => null,
  clearFilters: () => null,
};

const getKeywordPredicate =
  (keyword: string) => (product: ProductComponentType) => {
    if (!keyword) return true;
    const pattern = new RegExp(
      keyword
        .split("-")
        .map((word) => `(?=.*${word})`)
        .join("")
    );
    return pattern.test(product.title.toLowerCase());
  };

const getCategoryPredicate =
  (category: string) => (product: ProductComponentType) => {
    if (!category) return true;
    return (
      ((product as any).category && (product as any).category.toLowerCase() === category.toLowerCase()) ||
      (product.title || "").toLowerCase().includes(category.toLowerCase()) ||
      (product.type && String(product.type).toLowerCase().includes(category.toLowerCase()))
    );
  };

const getBrandPredicate =
  (brand: string) => (product: ProductComponentType) => {
    if (!brand) return true;
    return (
      ((product as any).brand && (product as any).brand.toLowerCase() === brand.toLowerCase()) ||
      (product.title || "").toLowerCase().includes(brand.toLowerCase())
    );
  };

interface FilterPredicateType<T> {
  (value: T, index: number, array: T[]): boolean | unknown;
}
const compose = <T extends unknown>(...predicates: FilterPredicateType<T>[]) =>
  predicates.reduceRight<FilterPredicateType<T>>(
    (acc, current) => (value, index, array) =>
      acc(value, index, array) && current(value, index, array),
    () => true
  );

const actions: { [type: string]: Function } = {
  page: () => () => true,
  keyword: getKeywordPredicate,
  category: getCategoryPredicate,
  brand: getBrandPredicate,
};

const ProductsContext = createContext<ProductStateType>(ProductsState);

export const useProductsState = () => useContext(ProductsContext);

function ProductsProvider(
  {
    products,
    children,
    preFilter = {},
    productImagePlaceholders,
  }: {
    products: ProductComponentType[];
    children: ReactNode;
    preFilter?: Partial<filterStateType>;
    productImagePlaceholders: ProductStateType["productImagePlaceholders"];
  },
  ref: ForwardedRef<{ updateFilterState: Function } | null>
) {
  const filterState = useRef<filterStateType>({
    ..._filterState,
    ...preFilter,
  });
  const sortByRef = useRef("");
  let params = new URLSearchParams();

  const getFilteredListings = () => {
    params = new URLSearchParams();
    const combinedPredicates = compose<ProductComponentType>(
      ...Object.keys(filterState.current)
        .filter((type) => type !== "page" && type !== "sort")
        .map((type) => {
          const value =
            filterState.current[type as keyof typeof filterState.current];
          if (value && typeof value === "string" && value.length > 0) {
            params.append(type, value);
            return actions[type](value);
          }
          return () => true;
        })
    );

    // Defensive: if `products` is undefined for any reason, treat as empty list
    return (products || []).filter(combinedPredicates);
  };

  const filterListings = (action: { [type: string]: unknown }) => {
    filterState.current = { ...filterState.current, ...action };
    setProductListing(getFilteredListings());
    const { page } = filterState.current;

    Router.replace(
      `/category/${page || "all"}?${params.toString()}`,
      undefined,
      {
        scroll: false,
        shallow: true,
      }
    );
  };

  const clearFilters = () => {
    const { page } = filterState.current;
    filterState.current = { ..._filterState, page };
    setProductListing(products || []);

    Router.replace(`/category/${page || "all"}`, undefined, {
      scroll: false,
      shallow: true,
    });
  };

  const sortListings = (sortBy: string) => {
    sortByRef.current = sortBy;

    let compare: (
      a: ProductComponentType,
      b: ProductComponentType
    ) => number = (aProduct, bProduct) =>
      new Date(bProduct.dateAdded).valueOf() -
      new Date(aProduct.dateAdded).valueOf();
    if (sortBy == "asc_price") {
      compare = (aProduct, bProduct) => aProduct.price - bProduct.price;
    } else if (sortBy == "price") {
      compare = (aProduct, bProduct) => bProduct.price - aProduct.price;
    } else if (sortBy == "asc_ratings") {
      compare = (aProduct, bProduct) => aProduct.ratings - bProduct.ratings;
    } else if (sortBy == "ratings") {
      compare = (aProduct, bProduct) => bProduct.ratings - aProduct.ratings;
    } else if (sortBy == "year_new") {
      compare = (aProduct, bProduct) =>
        (bProduct.year ?? 0) - (aProduct.year ?? 0);
    } else if (sortBy == "year_old") {
      compare = (aProduct, bProduct) =>
        (aProduct.year ?? 0) - (bProduct.year ?? 0);
    } else if (sortBy == "best") {
      compare = (aProduct, bProduct) =>
        bProduct.salesCount - aProduct.salesCount;
    }

    setProductListing((listings) => [...listings].sort(compare));
  };

  const [productListing, setProductListing] = useState(getFilteredListings());

  useImperativeHandle(ref, () => ({
    updateFilterState: (preFilter: Partial<filterStateType>) => {
      const filterStateUpdated = { ..._filterState, ...preFilter };

      if (!compareObjects(filterState.current, filterStateUpdated)) {
        filterState.current = filterStateUpdated;
        setProductListing(getFilteredListings());
        sortByRef.current = filterState.current.sort ?? "";
        if (sortByRef.current) sortListings(sortByRef.current);
      }
    },
  }));

  return (
    <ProductsContext.Provider
      value={{
        filterListings,
        sortListings,
        clearFilters,
        products: productListing,
        productImagePlaceholders,
        filterState: filterState.current,
        sortBy: sortByRef.current,
      }}
    >
      {children}
    </ProductsContext.Provider>
  );
}

export default forwardRef(ProductsProvider);
