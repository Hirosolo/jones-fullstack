# Jones (Jordan Ones) Store

### A Premium E-Commerce Experience for Sneaker Enthusiasts

Jones is a high-performance, SEO-optimized online marketplace specifically designed for purchasing Nike Jordan Ones. Built with a focus on speed, responsive design, and a premium user experience.

## Tech Stack

- **Framework**: [Next.js](https://nextjs.org/) (React)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [SASS (SCSS)](https://sass-lang.com/) with BEM methodology
- **Icons**: [React Icons](https://react-icons.github.io/react-icons/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [Prisma ORM](https://www.prisma.io/)
- **Auth**: [Iron Session](https://github.com/vvo/iron-session) (Cookie-based)
- **Payments**: [Stripe API](https://stripe.com/)
- **Notifications**: [React Toastify](https://fkhadra.github.io/react-toastify/)

---

## Setup Instructions

### 1. Environment Variables
Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL="postgres://{user}:{password}@{hostname}:{port}/{database_name}"

# Session
SECRET_COOKIE_PASSWORD="at_least_32_characters_long_secret"

# Stripe
STRIPE_PUBLISHABLE_KEY="pk_..."
STRIPE_SECRET_KEY="sk_..."
STRIPE_ENDPOINT_SECRET="whsec_..."
```

### 2. Installation
```bash
npm install
npx prisma db push
```

### 3. Run Development Server
```bash
npm run dev
```
Visit [http://localhost:3000](http://localhost:3000) to view the application.

---

