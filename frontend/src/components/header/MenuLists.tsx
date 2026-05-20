import Link from "next/link";
import { getPathString } from "src/utils";

const CategoriesData = require("@Data/CategoriesData.json");

// ── BRANDS raw data (for dynamic rendering in Header & Sidebar) ─────────────
export const brandsData: Record<string, string[]> = CategoriesData.brands;

// ── CATEGORIES ──────────────────────────────────────────────────────────────
export const categories: string[] = CategoriesData.categories;

export const CategoriesList = [
  <li key="view-all" className="sidebar__links-item sidebar__links-accordion">
    <Link href="/category">
      <a className="sidebar__anchor" style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
        VIEW ALL CATEGORIES
      </a>
    </Link>
  </li>,
  ...categories.map((name) => (
    <li key={name} className="sidebar__links-item sidebar__links-accordion">
      <Link href={`/products?category=${encodeURIComponent(name)}`}>
        <a className="sidebar__anchor" style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {name}
        </a>
      </Link>
    </li>
  ))
];
