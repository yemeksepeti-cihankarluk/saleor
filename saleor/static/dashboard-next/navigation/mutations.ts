import gql from "graphql-tag";
import { TypedMutation } from "../mutations";
import { menuDetailsFragment, menuItemNestedFragment } from "./queries";
import {
  MenuBulkDelete,
  MenuBulkDeleteVariables
} from "./types/MenuBulkDelete";
import { MenuCreate, MenuCreateVariables } from "./types/MenuCreate";
import { MenuDelete, MenuDeleteVariables } from "./types/MenuDelete";
import {
  MenuItemCreate,
  MenuItemCreateVariables
} from "./types/MenuItemCreate";
import { MenuUpdate, MenuUpdateVariables } from "./types/MenuUpdate";

const menuCreate = gql`
  mutation MenuCreate($input: MenuCreateInput!) {
    menuCreate(input: $input) {
      errors {
        field
        message
      }
      menu {
        id
      }
    }
  }
`;
export const MenuCreateMutation = TypedMutation<
  MenuCreate,
  MenuCreateVariables
>(menuCreate);

const menuBulkDelete = gql`
  mutation MenuBulkDelete($ids: [ID]!) {
    menuBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const MenuBulkDeleteMutation = TypedMutation<
  MenuBulkDelete,
  MenuBulkDeleteVariables
>(menuBulkDelete);

const menuDelete = gql`
  mutation MenuDelete($id: ID!) {
    menuDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const MenuDeleteMutation = TypedMutation<
  MenuDelete,
  MenuDeleteVariables
>(menuDelete);

const menuItemCreate = gql`
  ${menuItemNestedFragment}
  mutation MenuItemCreate($input: MenuItemCreateInput!) {
    menuItemCreate(input: $input) {
      errors {
        field
        message
      }
      menuItem {
        menu {
          id
          items {
            ...MenuItemNestedFragment
          }
        }
      }
    }
  }
`;
export const MenuItemCreateMutation = TypedMutation<
  MenuItemCreate,
  MenuItemCreateVariables
>(menuItemCreate);

const menuUpdate = gql`
  ${menuDetailsFragment}
  mutation MenuUpdate(
    $id: ID!
    $name: String!
    $moves: [MenuItemMoveInput]!
    $removeIds: [ID]!
  ) {
    menuUpdate(id: $id, input: { name: $name }) {
      errors {
        field
        message
      }
      menu {
        ...MenuDetailsFragment
      }
    }

    menuItemMove(menu: $id, moves: $moves) {
      errors {
        field
        message
      }
      menu {
        ...MenuDetailsFragment
      }
    }

    menuItemBulkDelete(ids: $removeIds) {
      errors {
        field
        message
      }
    }
  }
`;
export const MenuUpdateMutation = TypedMutation<
  MenuUpdate,
  MenuUpdateVariables
>(menuUpdate);
