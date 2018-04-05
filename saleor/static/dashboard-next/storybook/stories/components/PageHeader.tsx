import { storiesOf } from "@storybook/react";
import DeleteIcon from "material-ui-icons/Delete";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";

storiesOf("Generics / PageHeader", module)
  .add("without title", () => <PageHeader />)
  .add("with title", () => <PageHeader title="Lorem ipsum" />)
  .add("with title and back button", () => (
    <PageHeader title="Lorem ipsum" onBack={() => {}} />
  ))
  .add("with title icon bar", () => (
    <PageHeader title="Lorem ipsum">
      <IconButton>
        <DeleteIcon />
      </IconButton>
    </PageHeader>
  ))
  .add("with title, back button and icon bar", () => (
    <PageHeader title="Lorem ipsum" onBack={() => {}}>
      <IconButton>
        <DeleteIcon />
      </IconButton>
    </PageHeader>
  ));
