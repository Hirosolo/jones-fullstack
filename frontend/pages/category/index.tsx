import Link from "next/link";
import SEO from "@Components/common/SEO";
import { categories as staticCategories } from "@Components/header/MenuLists";
import { getPathString } from "src/utils";
import { ProductPlaceholderImg } from "src/constants";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CategoriesIndex({ categories }: { categories: any[] }) {
  return (
    <div>
      <SEO title="Categories" />
      <div className="container">
        <h1>All Categories</h1>
        <div className="categories-grid">
          {categories.map((c) => {
            const name = c.name || c;
            const num = c.num_product ?? c.num ?? 0;
            const image = c.image?.w400 || c.image?.url || c.image || null;
            return (
              <Link key={name} href={`/products?category=${encodeURIComponent(name)}`}>
                <a className="category-card">
                  <div className="category-card__img">
                    <img src={image || ProductPlaceholderImg} alt={name} />
                  </div>
                  <div className="category-card__body">
                    <div className="category-card__title">{name}</div>
                    <div className="category-card__count">{num} items</div>
                  </div>
                </a>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export async function getStaticProps() {
  // try backend categories endpoint, fallback to static list
  try {
    const res = await fetch(`${API_BASE}/api/categories/`);
    if (res.ok) {
      const data = await res.json();
      return { props: { categories: data } };
    }
  } catch (e) {
    // ignore
  }

  // fallback
  return { props: { categories: staticCategories.map((c) => ({ name: c, slug: getPathString(c), num_product: 0 })) } };
}

