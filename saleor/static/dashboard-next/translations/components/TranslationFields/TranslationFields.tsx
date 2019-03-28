import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import ArrowIcon from "@material-ui/icons/ArrowDropDown";
import classNames from "classnames";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Grid from "../../../components/Grid";
import Hr from "../../../components/Hr";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import TranslationFieldsLong from "./TranslationFieldsLong";
import TranslationFieldsRich from "./TranslationFieldsRich";
import TranslationFieldsShort from "./TranslationFieldsShort";

interface TranslationField {
  displayName: string;
  name: string;
  translation: string;
  type: "short" | "long" | "rich";
  value: string;
}

export interface TranslationFieldsProps {
  activeField: string;
  disabled: boolean;
  title: string;
  fields: TranslationField[];
  initialState: boolean;
  onEdit: (field: string) => void;
  onSubmit: (field: string, data: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    cardContent: {
      "&:last-child": {
        paddingBottom: theme.spacing.unit
      }
    },
    columnHeader: {
      marginBottom: theme.spacing.unit / 2
    },
    content: {
      "& a": {
        color: theme.palette.secondary.light
      },
      "& blockquote": {
        borderLeft: `2px solid ${theme.overrides.MuiCard.root.borderColor}`,
        margin: 0,
        padding: `${theme.spacing.unit}px ${theme.spacing.unit * 2}px`
      },
      "& h2": {
        fontSize: 22,
        marginBottom: theme.spacing.unit
      },
      "& h3": {
        fontSize: 19,
        marginBottom: theme.spacing.unit
      },
      "& p": {
        "&:last-child": {
          marginBottom: 0
        },
        marginBottom: theme.spacing.unit,
        marginTop: 0
      },
      paddingBottom: theme.spacing.unit * 2
    },
    editButtonContainer: {
      alignItems: "center",
      display: "flex",
      justifyContent: "flex-end"
    },
    fieldName: {
      color: theme.typography.caption.color,
      fontSize: 14,
      fontWeight: 500,
      marginBottom: theme.spacing.unit,
      marginTop: theme.spacing.unit * 2,
      textTransform: "uppercase"
    },
    grid: {
      gridRowGap: 0
    },
    hr: {
      gridColumnEnd: "span 2"
    },

    rotate: {
      transform: "rotate(180deg)"
    }
  });
const TranslationFields = withStyles(styles, { name: "TranslationFields" })(
  ({
    activeField,
    classes,
    disabled,
    fields,
    initialState,
    title,
    onEdit,
    onSubmit
  }: TranslationFieldsProps & WithStyles<typeof styles>) => {
    const [expanded, setExpandedState] = React.useState(initialState);

    return (
      <Card>
        <CardTitle
          title={title}
          toolbar={
            <IconButton onClick={() => setExpandedState(!expanded)}>
              <ArrowIcon
                className={classNames({
                  [classes.rotate]: expanded
                })}
              />
            </IconButton>
          }
        />
        {expanded && (
          <CardContent className={classes.cardContent}>
            <Grid className={classes.grid} variant="uniform">
              <Typography className={classes.columnHeader} variant="body1">
                {i18n.t("Original String")}
              </Typography>
              <Typography className={classes.columnHeader} variant="body1">
                {i18n.t("Translation", {
                  context: "translation to language"
                })}
              </Typography>
              {fields.map(field => (
                <>
                  <Hr className={classes.hr} />
                  <Typography className={classes.fieldName} variant="body1">
                    {field.displayName}
                  </Typography>
                  <div className={classes.editButtonContainer}>
                    <Button color="primary" onClick={() => onEdit(field.name)}>
                      {i18n.t("Edit")}
                    </Button>
                  </div>
                  <Typography className={classes.content}>
                    {field && field.value !== undefined ? (
                      field.type === "short" ? (
                        <TranslationFieldsShort
                          disabled={disabled}
                          edit={false}
                          initial={field.value}
                          onSubmit={undefined}
                        />
                      ) : field.type === "long" ? (
                        <TranslationFieldsLong
                          disabled={disabled}
                          edit={false}
                          initial={field.value}
                          onSubmit={undefined}
                        />
                      ) : (
                        <TranslationFieldsRich
                          disabled={disabled}
                          edit={false}
                          initial={field.value}
                          onSubmit={undefined}
                        />
                      )
                    ) : (
                      <Skeleton />
                    )}
                  </Typography>
                  <Typography className={classes.content}>
                    {field && field.translation !== undefined ? (
                      field.type === "short" ? (
                        <TranslationFieldsShort
                          disabled={disabled}
                          edit={activeField === field.name}
                          initial={field.translation}
                          onSubmit={data => onSubmit(field.name, data)}
                        />
                      ) : field.type === "long" ? (
                        <TranslationFieldsLong
                          disabled={disabled}
                          edit={activeField === field.name}
                          initial={field.translation}
                          onSubmit={data => onSubmit(field.name, data)}
                        />
                      ) : (
                        <TranslationFieldsRich
                          disabled={disabled}
                          edit={activeField === field.name}
                          initial={field.translation}
                          onSubmit={data => onSubmit(field.name, data)}
                        />
                      )
                    ) : (
                      <Skeleton />
                    )}
                  </Typography>
                </>
              ))}
            </Grid>
          </CardContent>
        )}
      </Card>
    );
  }
);
TranslationFields.displayName = "TranslationFields";
export default TranslationFields;
