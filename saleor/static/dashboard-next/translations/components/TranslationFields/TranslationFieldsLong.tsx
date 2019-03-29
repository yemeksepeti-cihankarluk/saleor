import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Form from "../../../components/Form";
import i18n from "../../../i18n";
import TranslationFieldsSave from "./TranslationFieldsSave";

interface TranslationFieldsLongProps {
  disabled: boolean;
  edit: boolean;
  initial: string;
  saveButtonState: ConfirmButtonTransitionState;
  onSubmit: (data: string) => void;
}

const TranslationFieldsLong: React.FC<TranslationFieldsLongProps> = ({
  disabled,
  edit,
  initial,
  saveButtonState,
  onSubmit
}) =>
  edit ? (
    <Form
      initial={{ translation: initial }}
      onSubmit={data => onSubmit(data.translation)}
    >
      {({ change, data, reset, submit }) => (
        <div>
          <TextField
            disabled={disabled}
            fullWidth
            multiline
            // label={i18n.t("Translation")}
            name="translation"
            value={data.translation}
            onChange={change}
          />
          <TranslationFieldsSave
            saveButtonState={saveButtonState}
            onDiscard={reset}
            onSave={submit}
          />
        </div>
      )}
    </Form>
  ) : initial === null ? (
    <Typography color="textSecondary">
      {i18n.t("No translation yet")}
    </Typography>
  ) : (
    initial
  );
TranslationFieldsLong.displayName = "TranslationFieldsLong";
export default TranslationFieldsLong;
