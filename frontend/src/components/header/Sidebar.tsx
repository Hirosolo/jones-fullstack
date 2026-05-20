import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { BsCart3, BsXLg } from "react-icons/bs";
import { FiSearch, FiLogOut, FiLogIn } from "react-icons/fi";
import { IoIosArrowForward, IoIosArrowBack } from "react-icons/io";
import { BiCaretDown } from "react-icons/bi";

import Form from "@Components/common/Form";
import { CategoriesList, brandsData } from "./MenuLists";
import { getPathString } from "src/utils";

import { useDialog, DialogType, useCurrencyFormatter } from "@Contexts/UIContext";
import { useAuthState } from "@Contexts/AuthContext";
import useTabTrapIn from "@Hooks/useKeyTrap";
import Animate from "@Components/common/Animate";

type BrandsLevel = null | "groups" | string; // null = not in brands, "groups" = showing groups, string = group name

export default function Sidebar() {
  const format = useCurrencyFormatter();

  // General submenu (for CATEGORIES)
  const [submenu, setSubmenu] = useState<Array<any> | null>(null);
  const [submenuActive, setSubmenuActive] = useState<boolean>(false);

  // Brands-specific two-level navigation
  const [brandsLevel, setBrandsLevel] = useState<BrandsLevel>(null);

  const { currentDialog, setDialog } = useDialog();

  const { user } = useAuthState();
  const isAuth = user.isAuth;
  const cartCount = user.cart.count;
  const cartTotal = user.cart.total;

  const sidebarRef = useRef<HTMLDivElement>(null);
  const sidebarVisible = currentDialog == DialogType.SIDEBAR_DIALOG;
  useTabTrapIn(sidebarRef.current, sidebarVisible);

  // When slide-back animation finishes, clear submenu & brandsLevel
  useEffect(() => {
    setTimeout(() => {
      if (!submenuActive) {
        setSubmenu(null);
        setBrandsLevel(null);
      }
    }, 600);
  }, [submenuActive]);

  const openBrands = () => {
    setBrandsLevel("groups");
    setSubmenuActive(true);
  };

  const openBrandGroup = (group: string) => {
    setBrandsLevel(group);
  };

  const backFromBrandGroup = () => {
    setBrandsLevel("groups");
  };

  const backFromSubmenu = () => {
    setSubmenuActive(false);
  };

  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);

  // Render the content inside the submenu panel
  const renderSubmenuContent = () => {
    if (brandsLevel === "groups") {
      // Brands panel with accordion for groups
      return (
        <>
          <li className="sidebar__links-item sidebar__back-button">
            <button onClick={backFromSubmenu}>
              <IoIosArrowBack />
              <span>BACK</span>
            </button>
          </li>
          <li className="sidebar__links-item sidebar__links-group-label">
            <span>BRANDS</span>
          </li>
          {Object.entries(brandsData).map(([group, brands]) => {
            const isOpen = expandedGroup === group;
            return (
              <li key={group} className={`sidebar__links-item sidebar__links-accordion${isOpen ? " sidebar__links-accordion--open" : ""}`}>
                <button onClick={() => setExpandedGroup(isOpen ? null : group)}>
                  <span>{group}</span>
                  <BiCaretDown className={`sidebar__accordion-caret${isOpen ? " sidebar__accordion-caret--up" : ""}`} />
                </button>
                {isOpen && (
                  <ul className="sidebar__accordion-items">
                    {brands.map((brand) => (
                      <li key={brand}>
                        <Link href={`/brand/${getPathString(brand)}`}>
                          <a onClick={() => setDialog(null)}>{brand}</a>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </>
      );
    }

    // Default: regular submenu (categories)
    return (
      <>
        <li className="sidebar__links-item sidebar__back-button">
          <button onClick={backFromSubmenu}>
            <IoIosArrowBack />
            <span>BACK</span>
          </button>
        </li>
        {submenu}
      </>
    );
  };

  return (
    <Animate isMounted={sidebarVisible} unmountDelay={300}>
      <div className="sidebar" onClick={() => setDialog(null)}>
        <button aria-label="close sidebar" className="sidebar__close">
          <BsXLg className="sidebar__close-icon" />
        </button>
        <nav
          className={`sidebar__nav${submenuActive ? " sidebar__nav--submenu" : ""}`}
          onClick={(e) => e.stopPropagation()}
        >
          <div ref={sidebarRef} className="sidebar__container">
            <button
              onClick={() => setDialog(DialogType.SEARCH_BOX)}
              className="sidebar__search-box"
            >
              <span className="sidebar__search-box-label">Search Jones Store</span>
              <span className="sidebar__search-box-icon">
                <FiSearch />
              </span>
            </button>
            <div className="sidebar__links">
              <ul>
                <li className="sidebar__links-item">
                  <Link href="/">
                    <a className="sidebar__anchor">HOME</a>
                  </Link>
                </li>
                <li className="sidebar__links-item sidebar__links-menu">
                  <button
                    onClick={() => {
                      setSubmenu(CategoriesList);
                      setBrandsLevel(null);
                      setSubmenuActive(true);
                    }}
                  >
                    <span>CATEGORIES</span>
                    <IoIosArrowForward />
                  </button>
                </li>
                <li className="sidebar__links-item sidebar__links-menu">
                  <button onClick={openBrands}>
                    <span>BRANDS</span>
                    <IoIosArrowForward />
                  </button>
                </li>
                <li className="sidebar__links-item">
                  <Link href="/about">
                    <a className="sidebar__anchor">ABOUT US</a>
                  </Link>
                </li>
                <li className="sidebar__links-item">
                  <Link href="/contact">
                    <a className="sidebar__anchor">CONTACT US</a>
                  </Link>
                </li>
              </ul>
            </div>
            <div className="sidebar__icon-links">
              <ul>
                <li className="sidebar__icon-links-item">
                  {isAuth ? (
                    <Form
                      afterSubmit={(data) => {
                        if (data.success) {
                          location.reload();
                        }
                      }}
                      action="/api/auth/signout"
                    >
                      <button
                        aria-label="logout"
                        className="sidebar__link-btn"
                        type="submit"
                      >
                        <FiLogOut />
                        Logout
                      </button>
                    </Form>
                  ) : (
                    <Link href="/signin">
                      <a className="sidebar__anchor">
                        <FiLogIn />
                        <span>Sign In</span>
                      </a>
                    </Link>
                  )}
                </li>
                <li className="sidebar__icon-links-item">
                  <button
                    aria-label="cart"
                    onClick={() => setDialog(DialogType.CART)}
                    className="sidebar__anchor"
                  >
                    <BsCart3 />
                    <span>
                      Cart
                      {cartCount
                        ? ` (${cartCount}) (${format(cartTotal)})`
                        : ""}
                    </span>
                  </button>
                </li>
              </ul>
            </div>
            <div className="sidebar__lang-currency language-currency">
              <button className="language-currency__btn">
                {"English"} <span className="language-currency__sep">|</span>{" "}
                {"$ USD"}
              </button>
            </div>
          </div>

          <div className="sidebar__container sidebar__submenu-container">
            <div className="sidebar__links-2">
              <ul hidden={submenu == null && brandsLevel == null}>
                {renderSubmenuContent()}
              </ul>
            </div>
          </div>
        </nav>
      </div>
    </Animate>
  );
}
