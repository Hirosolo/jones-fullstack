import type { ProductComponentType } from "src/types/shared";
import { NextPage, GetServerSideProps } from "next";
import SEO from "@Components/common/SEO";
import Constraints from "@Components/products/constraints";
import ProductsGrid from "@Components/products/ProductsGrid";
import { MOCK_PRODUCTS } from "@Lib/mockData";

const SearchPage: NextPage<SearchPageType> = ({ query, products, count }) => {
  return (
    <div>
      <SEO title={`"${query}"`} />
      <Constraints
        isSearch
        allProductsCount={count}
        currentProductsCount={products.length}
      />

      <div className="results">
        <div className={"results__container"}>
          <ProductsGrid products={products} />
        </div>
      </div>
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async ({ query }) => {
  const { search = "", q = "" } = query;
  const searchQuery = (search || q) as string;

  const results = MOCK_PRODUCTS.filter(product => 
    product.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return {
    props: {
      query: searchQuery,
      products: results,
      count: results.length,
    },
  };
};

export default SearchPage;

interface SearchPageType {
  query: string;
  products: ProductComponentType[];
  count: number;
}
