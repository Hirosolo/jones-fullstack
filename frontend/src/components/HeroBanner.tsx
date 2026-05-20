import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/router";
import { RiRadioButtonLine, RiCheckboxBlankCircleFill } from "react-icons/ri";

import { useAnnouncementState } from "@Contexts/UIContext";
import useMouseCoords from "@Hooks/useMouseCoords";
import useScrollTop from "@Hooks/useScrollTop";
import { range } from "src/utils";
import SocialIcons from "./common/SocialButtons";

import BannerImage1 from "@Images/acdc-hoodie-banner.webp";
import BannerImage2 from "@Images/monsterEnergy-cap-banner.webp";
import BannerImage3 from "@Images/starWar-cup-banner.webp";
import { MoonLoader } from "react-spinners";

const VIEWS_COUNT = 3;
const INTERVAL = 6000;

export default function HeroBanner() {
  const [activeView, setActiveView] = useState(VIEWS_COUNT - 1);
  const bannerRef = useRef<HTMLDivElement>(null);
  const rAFRef = useRef(0);
  const router = useRouter();

  const announcementVisible = useAnnouncementState();
  const [x, y] = useMouseCoords(bannerRef.current, 25, 100);
  const scrollTop = useScrollTop();

  const short = router.pathname != "/";

  useEffect(() => {
    if (!!bannerRef.current) {
      let currentTime = performance.now();

      rAFRef.current = requestAnimationFrame(function changeSlide(tick) {
        if (tick - currentTime > INTERVAL) {
          setActiveView((activeView + 1) % VIEWS_COUNT);
          currentTime = tick;
        }
        rAFRef.current = requestAnimationFrame(changeSlide);
      });
      return () => cancelAnimationFrame(rAFRef.current);
    }
  }, [activeView]);

  return (
    <section
      id="main-banner"
      className={
        "banner" +
        (short ? " banner--short" : "") +
        (announcementVisible ? " banner--with-announcement" : "")
      }
    >
      <div ref={bannerRef} className="banner__container">
        <div className="banner__background"></div>
        {short ? null : (
          <>
            <div className="banner__indicators">
              {range(0, slidesData.length - 1).map((_, i) => (
                <button
                  aria-label={"slide " + (i + 1)}
                  key={"indicator" + i}
                  onClick={() => setActiveView(i)}
                  className={
                    "banner__indicator" +
                    (activeView == i ? " banner__indicator--active" : "")
                  }
                >
                  {activeView == i ? (
                    <RiRadioButtonLine />
                  ) : (
                    <RiCheckboxBlankCircleFill />
                  )}
                </button>
              ))}
            </div>

            <div className="banner__social-links">
              <SocialIcons vertical />
            </div>

            <div className="banner__main">
              {!!bannerRef.current ? (
                <>
                  {slidesData.map((data, i) => (
                    <div
                      key={data.title + data.type}
                      className={
                        "banner__content" +
                        (activeView == i ? " banner__content--active" : "")
                      }
                    >
                      <div className="banner__headings">
                        <p className="banner__secondary-text">
                          <span>{data.secondary.highlighted}</span>{" "}
                          {data.secondary.text}
                        </p>
                        <h2
                          style={{
                            transform: `translate3d(${-x * 0.2}px, 0, 0)`,
                          }}
                          className="banner__title-type"
                        >
                          <span>{data.type}</span>
                        </h2>
                        <h3 className="banner__title">
                          <span>{data.title}</span>
                        </h3>
                      </div>
                      <div
                        style={{
                          transform: `translate3d(${-x * 0.8}px, ${-y * 0.4 + scrollTop * 0.1
                            }px, 0)`,
                        }}
                        className="banner__image"
                      >
                        <Image
                          className="banner__image-element"
                          layout="responsive"
                          width={data.imageSrc.width}
                          height={data.imageSrc.height}
                          src={data.imageSrc}
                          priority
                          alt=""
                        />
                      </div>
                    </div>
                  ))}
                  <div className="banner__action-button">
                    <Link href={slidesData[activeView].url}>
                      <a className="banner__action-button-link">
                        <span>buy yours</span>
                      </a>
                    </Link>
                  </div>
                </>
              ) : (
                <div className="banner__loader">
                  <MoonLoader color="#fff" className="banner__loader-spinner" />
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

const slidesData = [
  {
    secondary: { highlighted: "exclusive", text: "premium apparel" },
    type: "signature",
    title: "collections",
    imageSrc: BannerImage1,
    url: "/category/clothing",
  },
  {
    secondary: { highlighted: "new", text: "arrivals" },
    type: "modern",
    title: "accessories",
    imageSrc: BannerImage3,
    url: "/category/accessories",
  },
  {
    secondary: { highlighted: "vintage", text: "aesthetic" },
    type: "classic",
    title: "home decor",
    imageSrc: BannerImage2,
    url: "/category/home-decor",
  },
];
