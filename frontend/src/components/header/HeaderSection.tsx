import { useEffect, useRef, useState } from "react";
import { Router } from "next/router";

import Link from "next/link";
import { BsCart3 } from "react-icons/bs";
import { FiSearch, FiMenu } from "react-icons/fi";
import { BiCaretDown } from "react-icons/bi";
import { IoIosArrowForward } from "react-icons/io";

import Logo from "@Components/common/Logo";
import ToolTip from "@Components/common/ToolTip";
import { CategoriesList, brandsData, categories } from "./MenuLists";
import { getPathString } from "src/utils";

import useScrollTop from "@Hooks/useScrollTop";
import { DialogType, useCurrencyFormatter, useDialog } from "@Contexts/UIContext";
import { useAuthState } from "@Contexts/AuthContext";

type DropdownMode = "categories" | "brands" | null;

export default function HeaderSection() {
  const { setDialog } = useDialog();

  const [dropdownMode, setDropdownMode] = useState<DropdownMode>(null);
  const [expandedBrandsGroup, setExpandedBrandsGroup] = useState<string | null>(null);
  const [activeBrandsGroup, setActiveBrandsGroup] = useState<string | null>(null);
  const [pinnedState, setPinnedState] = useState(false);
  const scrollTop = useScrollTop();
  const headerRef = useRef<HTMLElement>(null);
  const format = useCurrencyFormatter();
  const { user } = useAuthState();
  const cartCount = user.cart.count;
  const cartTotal = user.cart.total;

  useEffect(() => {
    const mainBanner = document.getElementById("main-banner");
    if (mainBanner) {
      setPinnedState(scrollTop > mainBanner.offsetTop + mainBanner.clientHeight);
    }
  }, [scrollTop]);

  useEffect(() => {
    const hideDropdown = () => {
      setDropdownMode(null);
      setExpandedBrandsGroup(null);
    };
    Router.events.on("routeChangeStart", hideDropdown);
    return () => Router.events.off("routeChangeStart", hideDropdown);
  }, []);

  const [hoveredElement, setHoveredElement] = useState<string>("");

  const toggleDropdown = (mode: DropdownMode) => {
    if (dropdownMode === mode) {
      setDropdownMode(null);
    } else {
      setDropdownMode(mode);
      if (mode === "brands") {
        // Initialize with the first group if none active
        const groups = Object.keys(brandsData);
        if (groups.length > 0 && !activeBrandsGroup) {
          setActiveBrandsGroup(groups[0]);
        }
      }
      setExpandedBrandsGroup(null);
    }
  };

  return (
    <>
      <header
        ref={headerRef}
        className={`header${pinnedState ? " header--pinned" : ""}`}
      >
        <div className="header__container">
          <div className="header__menu-button">
            <button
              aria-label="menu"
              className="header__menu-toggle"
              onClick={() => setDialog(DialogType.SIDEBAR_DIALOG)}
            >
              <FiMenu />
            </button>
          </div>

          <div className="header__logo">
            <Logo />
          </div>

          <div className="header__nav">
            <nav>
              <ul>
                <li className="header__nav-link">
                  <Link href="#">
                    <a
                      onClick={(e) => {
                        e.preventDefault();
                        toggleDropdown("categories");
                      }}
                    >
                      CATEGORIES <BiCaretDown className="header__nav-caret" />
                    </a>
                  </Link>
                </li>
                <li className="header__nav-link">
                  <Link href="#">
                    <a
                      onClick={(e) => {
                        e.preventDefault();
                        toggleDropdown("brands");
                      }}
                    >
                      BRANDS <BiCaretDown className="header__nav-caret" />
                    </a>
                  </Link>
                </li>
                <li className="header__nav-link">
                  <Link href="/about">
                    <a>ABOUT US</a>
                  </Link>
                </li>
                <li className="header__nav-link">
                  <Link href="/contact">
                    <a>CONTACT US</a>
                  </Link>
                </li>
              </ul>
            </nav>
          </div>

          <div className="header__buttons">
            <ul>
              <li className="header__button header__button-search">
                <Link href="./#">
                  <a
                    className="header__button-link"
                    onClick={(e) => {
                      e.preventDefault();
                      setDialog(DialogType.SEARCH_BOX);
                    }}
                  >
                    <FiSearch />
                  </a>
                </Link>
              </li>
              <li className="header__button header__button-cart">
                <button
                  aria-label="cart"
                  onClick={() => setDialog(DialogType.CART)}
                  onPointerEnter={(e) => setHoveredElement("header-cart-btn")}
                  onPointerLeave={(e) => setHoveredElement("")}
                  className="header__button-link"
                  id="header-cart-btn"
                >
                  <BsCart3 />
                  <ToolTip currentId={hoveredElement} hoverElementId="header-cart-btn">
                    {cartCount ? (
                      <span style={{ fontWeight: "400", userSelect: "none" }}>
                        {format(cartTotal)}
                      </span>
                    ) : (
                      "Empty"
                    )}
                  </ToolTip>
                </button>
                {cartCount ? <span>{cartCount}</span> : null}
              </li>
            </ul>
          </div>
        </div>
      </header>

      <div
        className={
          "header__dropdown" +
          (dropdownMode ? " header__dropdown--visible" : "") +
          (pinnedState ? " header__dropdown--pinned" : "")
        }
      >
        {/* ── CATEGORIES: Grid Layout ──────────────────────────────── */}
        {dropdownMode === "categories" && (
            <div className="header__brands-accordion header__categories-grid">
            <div className="header__brands-group">
              <Link href="/category">
                <a className="header__brands-group-btn header__brands-group-btn--link">
                  VIEW ALL CATEGORIES
                </a>
              </Link>
            </div>
            {categories.map((name: string) => (
              <div key={name} className="header__brands-group">
                <Link href={`/products?category=${encodeURIComponent(name)}`}>
                  <a className="header__brands-group-btn header__brands-group-btn--link">
                    {name}
                  </a>
                </Link>
              </div>
            ))}
          </div>
        )}

        {/* ── BRANDS: Two-Pane Layout ───────────────────────────────── */}
        {dropdownMode === "brands" && (
          <div className="header__brands-two-pane">
            <div className="header__brands-sidebar">
              <div className="header__brands-sidebar-item">
                <Link href="/brand">
                  <a className="header__brands-group-btn header__brands-group-btn--link">
                    VIEW ALL BRANDS
                  </a>
                </Link>
              </div>
              {Object.keys(brandsData).map((group) => (
                <button
                  key={group}
                  className={`header__brands-sidebar-item${
                    activeBrandsGroup === group ? " active" : ""
                  }`}
                  onMouseEnter={() => setActiveBrandsGroup(group)}
                >
                  {group}
                  <IoIosArrowForward className="header__brands-sidebar-icon" />
                </button>
              ))}
            </div>
            <div className="header__brands-content">
              <div className="header__brands-content-grid">
                {activeBrandsGroup &&
                  brandsData[activeBrandsGroup]?.map((brand) => (
                    <div key={brand} className="header__brands-content-item">
                      <Link href={`/products?brand=${encodeURIComponent(brand)}`}>
                        <a>{brand}</a>
                      </Link>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
