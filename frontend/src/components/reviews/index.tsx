import Link from "next/link";
import { useState, useEffect } from "react";
import type { User, Review as ReviewType } from "src/types/shared";

import Button from "../formControls/Button";
import TextField from "../formControls/TextField";
import Form from "../common/Form";
import RatingStars from "../common/RatingStars";
import Modal from "../Modal";
import Review from "./Review";

import { useAuthState } from "@Contexts/AuthContext";

export default function Reviews({ productId }: PropTypes) {
  const [reviewModal, setReviewModal] = useState(false);
  const [reviews, setReviews] = useState<(ReviewType & { user: User })[]>([]);
  const [loading, setLoading] = useState(true);

  const { user } = useAuthState();

  useEffect(() => {
    // Frontend only: Return empty or mock reviews
    setReviews([]);
    setLoading(false);
  }, [productId]);

  const averageRatings =
    reviews.reduce((total, { rating }) => total + rating, 0) /
    (reviews.length || 1);

  if (loading) {
    return (
      <div className="product-details__panel product-details__reviews-panel">
        <p className="product-details__prompt">Please wait while loading reviews...</p>
      </div>
    );
  }

  return (
    <div className="product-details__panel product-details__reviews-panel">
      {user?.isAuth ? (
        <>
          <Button onClick={() => setReviewModal(true)}>Write A Review</Button>{" "}
          <Modal
            title="Write Review"
            visible={reviewModal}
            onClose={() => setReviewModal(false)}
          >
            <div className="product-details__reviews-form">
              <Form
                method="POST"
                action={`#`}
                afterSubmit={(data) => {
                  alert("Review submitted (Mock)");
                  setReviewModal(false);
                }}
              >
                <RatingStars interactive />
                <TextField name="body" multiline label="Your review" />
                <Button>Submit Review</Button>
              </Form>
            </div>
          </Modal>{" "}
        </>
      ) : (
        <p className="product-details__prompt">
          Please{" "}
          <Link href="/signin">
            <a className="product-details__link">login</a>
          </Link>{" "}
          to submit a review.
        </p>
      )}
      <div className="reviews">
        <div className="reviews__avg-ratings">
          Average Rating: <RatingStars count={averageRatings} />{" "}
          {averageRatings.toFixed(1)} ({reviews.length} Customer Reviews)
        </div>
        <ul className="reviews__list">
          {reviews.map((review) => (
            <li
              key={review.userId + review.productId}
              className="reviews__item"
            >
              <Review {...review} />
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

interface PropTypes {
  productId: string;
}
