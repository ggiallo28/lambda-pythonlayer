# MuG::Lambda::PythonLayer

An example resource schema demonstrating some basic constructs and validation rules.

## Syntax

To declare this entity in your AWS CloudFormation template, use the following syntax:

### JSON

<pre>
{
    "Type" : "MuG::Lambda::PythonLayer",
    "Properties" : {
        "<a href="#name" title="Name">Name</a>" : <i>String</i>,
        "<a href="#s3bucket" title="S3Bucket">S3Bucket</a>" : <i>String</i>,
        "<a href="#requirements" title="Requirements">Requirements</a>" : <i>[ String, ... ]</i>,
    }
}
</pre>

### YAML

<pre>
Type: MuG::Lambda::PythonLayer
Properties:
    <a href="#name" title="Name">Name</a>: <i>String</i>
    <a href="#s3bucket" title="S3Bucket">S3Bucket</a>: <i>String</i>
    <a href="#requirements" title="Requirements">Requirements</a>: <i>
      - String</i>
</pre>

## Properties

#### Name

A unique Name for the AWS Lambda Layer

_Required_: Yes

_Type_: String

_Pattern_: <code>^[A-Z]{3,5}[0-9]{8}-[0-9]{4}$</code>

_Update requires_: [No interruption](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-no-interrupt)

#### S3Bucket

The name of the Amazon S3 Bucket used to upload assets.

_Required_: Yes

_Type_: String

_Update requires_: [No interruption](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-no-interrupt)

#### Requirements

List of packages to install.

_Required_: Yes

_Type_: List of String

_Update requires_: [No interruption](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-no-interrupt)

## Return Values

### Ref

When you pass the logical ID of this resource to the intrinsic `Ref` function, Ref returns the Name.

### Fn::GetAtt

The `Fn::GetAtt` intrinsic function returns a value for a specified attribute of this type. The following are the available attributes and sample return values.

For more information about using the `Fn::GetAtt` intrinsic function, see [Fn::GetAtt](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html).

#### LayerArn

Returns the <code>LayerArn</code> value.

#### LayerVersionArn

Returns the <code>LayerVersionArn</code> value.

#### Version

Returns the <code>Version</code> value.

