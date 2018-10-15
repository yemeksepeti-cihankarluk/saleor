import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import {
  CategoryDetails,
  CategoryDetailsVariables
} from "./types/CategoryDetails";
import { RootCategories } from "./types/RootCategories";

export const rootCategories = gql`
  query RootCategories {
    categories(level: 0) {
      edges {
        node {
          id
          name
          children {
            totalCount
          }
          products {
            totalCount
          }
        }
      }
    }
  }
`;
export const TypedRootCategoriesQuery = TypedQuery<RootCategories, {}>(
  rootCategories
);

export const categoryDetails = gql`
  query CategoryDetails(
    $id: ID!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    category(id: $id) {
      id
      name
      description
      parent {
        id
      }
      children {
        edges {
          node {
            id
            name
            children {
              totalCount
            }
            products {
              totalCount
            }
          }
        }
      }
      products(first: $first, after: $after, last: $last, before: $before) {
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
        edges {
          cursor
          node {
            id
            name
            thumbnailUrl
            productType {
              id
              name
            }
          }
        }
      }
    }
  }
`;
export const TypedCategoryDetailsQuery = TypedQuery<
  CategoryDetails,
  CategoryDetailsVariables
>(categoryDetails);
