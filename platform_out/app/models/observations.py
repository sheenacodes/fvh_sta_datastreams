from app import db
from flask import current_app
import logging
from enum import Enum
from app.models.datastreams import Datastreams
from app.models.foi import FeaturesofInterest
import json
import datetime
from sqlalchemy import cast, Float
from datetime import datetime

logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
    level=current_app.config["LOG_LEVEL"],
)

# TODO ?
# class ExpandType(Enum):
#     Neither = 0
#     Datastream = 1
#     FeatureOfInterest = 2
#     Both = 3


class Observations(db.Model):
    __tablename__ = "observation"
    id = db.Column(db.Integer, primary_key=True)
    phenomenontime_begin = db.Column(db.DateTime(), index=True)
    phenomenontime_end = db.Column(db.DateTime(), index=True)
    resulttime = db.Column(db.DateTime(), index=True)
    result = db.Column(db.String(), index=True)
    resultquality = db.Column(db.String(), index=True)
    validtime_begin = db.Column(db.DateTime(), index=True)
    validtime_end = db.Column(db.DateTime(), index=True)
    resultquality = db.Column(db.String(), index=True)
    # parameters = db.Column(JsonEncodedDict)
    # parameters = db.Column(MutableDict.as_mutable(JSON))
    datastream_id = db.Column(db.Integer, index=True)
    featureofintrest_link = db.Column(db.String(), index=True)
    featureofinterest_id = db.Column(db.Integer(), index=True)

    def __repr__(self):
        return f"<Observation {self.result}, {self.resulttime}>"

    @classmethod
    def to_json(cls, x):
        """
        returns observations in json format
        """
        return {
            "@iot.id": x.id,
            "@iot.selfLink": f"{current_app.config['HOSTED_URL']}/Observations({x.id})",
            "phenomenonTimeBegin": x.phenomenontime_begin.strftime("%d-%m-%YT%H:%M:%SZ")
            if x.phenomenontime_begin
            else None,
            "phenomenonTimeEnd": x.phenomenontime_end.strftime("%d-%m-%YT%H:%M:%SZ")
            if x.phenomenontime_end
            else None,
            "resultTime": x.resulttime.strftime("%d-%m-%YT%H:%M:%SZ")
            if x.resulttime
            else None,
            "result": x.result,
            "Datastream@iot.navigationLink": f"{current_app.config['HOSTED_URL']}/Observations({x.id})/Datastreams",
            "FeatureOfInterest@iot.navigationLink": f"{current_app.config['HOSTED_URL']}/Observations({x.id})/FeatureOfInterest"
            if x.featureofinterest_id
            else None,
        }

    @classmethod
    def to_dataarray(cls, x):
        """
        returns observations in json format
        """
        return [
            x.id,
            x.phenomenontime_begin.strftime("%d-%m-%YT%H:%M:%SZ")
            if x.phenomenontime_begin
            else None,
            x.result,
            x.resulttime.strftime("%d-%m-%YT%H:%M:%SZ") if x.resulttime else None,
        ]

    @classmethod
    def to_selected_json(cls, x, selectparams):
        """
        returns selected fields of observations in json format
        """
        datadict = Observations.to_json(x)

        if selectparams:
            key_dict = {
                "datastream": "Datastream@iot.navigationLink",
                "featureofinterest": "FeatureOfInterest@iot.navigationLink",
                "phenomenontimebegin": "phenomenonTimeBegin",
                "phenomenontimeend": "phenomenonTimeEnd",
                "result": "result",
                "resulttime": "resultTime",
            }

            new_result = {}
            for key in selectparams:
                new_result[key_dict[key]] = datadict[key_dict[key]]

            datadict = new_result

        return datadict

    @classmethod
    def to_expanded_datastream_json(cls, data_dict, x):
        """
        returns Observations json with Datastreams expanded as its own json object
        """
        del data_dict["Datastream@iot.navigationLink"]
        data_dict["Datastream"] = {
            "@iot.id": x.datastream_id,
            "@iot.selfLink": f"{current_app.config['HOSTED_URL']}/Datastreams({x.datastream_id})",
            "description": x.ds_name,
            "name": x.ds_description,
            "unitOfMeasurement": x.ds_unitofmeasurement,
            "Observations@iot.navigationLink": f"{current_app.config['HOSTED_URL']}/Datastreams({x.datastream_id})/Observations",
            "Sensor@iot.navigationLink": f"{current_app.config['HOSTED_URL']}/Datastreams({x.datastream_id})/Sensor",
            "Thing@iot.navigationLink": f"{current_app.config['HOSTED_URL']}/Datastreams({x.datastream_id})/Thing",
        }
        return data_dict

    @classmethod
    def to_expanded_foi_json(cls, data_dict, x):
        """
        returns Observations json with FeatreOfInterest expanded as its own json object
        """
        del data_dict["FeatureOfInterest@iot.navigationLink"]
        if x.featureofinterest_id:
            data_dict["FeatureOfInterest"] = {
                "@iot.id": x.featureofinterest_id,
                "@iot.selfLink": f"{current_app.config['HOSTED_URL']}/FeaturesOfInterest({x.featureofinterest_id})",
                "name": x.foi_name,
                "description": x.foi_description,
                "encodingtype": x.foi_encodingtype,
                "feature": json.loads(x.foi_feature),
                "Observations@iot.navigationLink": f"{current_app.config['HOSTED_URL']}/FeaturesOfInterest({x.featureofinterest_id})/Observations",
            }
        else:
            data_dict["FeatureOfInterest"] = None
        return data_dict

    @classmethod
    def expand_to_selected_json(cls, x, expand_code, selects):
        """
        applies expansion of fields as per expand code given
        """
        result = Observations.to_selected_json(x, selects)

        if selects is None:
            select_datastream = True
            select_foi = True
        else:
            select_datastream = True if ("datastream" in selects) else False
            select_foi = True if ("featureofinterest" in selects) else False

        if (expand_code == 1 or expand_code == 3) and select_datastream:
            result = Observations.to_expanded_datastream_json(result, x)
        if (expand_code == 2 or expand_code == 3) and select_foi:
            result = Observations.to_expanded_foi_json(result, x)

        return result

    # @classmethod
    # def expand_to_json(cls, x, expand_code):
    #     """
    #     applies expansion of fields as per expand code given
    #     """
    #     result = Observations.to_json(x)

    #     if expand_code == 1 or expand_code == 3:
    #         result = Observations.to_expanded_datastream_json(result, x)
    #     if expand_code == 2 or expand_code == 3:
    #         result = Observations.to_expanded_foi_json(result, x)

    #     return result

    @classmethod
    def get_nextlink_queryparams(cls, top, skip, expand_code, resultformat):
        """
        returns nextLink used for paginating based on current parameters
        """
        # TODO see if skip overreaches limit

        query_params = []
        if top:
            query_params.append(f"$top={top}")
        if skip >= 0:
            query_params.append(f"$skip={skip+100}")

        if resultformat:
            query_params.append(f"$resultformat={resultformat}")

        if expand_code > 0:
            expand_strings_list = []
            if expand_code == 1 or expand_code == 3:
                expand_strings_list.append("datastream")
            if expand_code == 2 or expand_code == 3:
                expand_strings_list.append("featureofinterest")

            query_params.append(f"$expand={','.join(expand_strings_list)}")

        url_string = f"?{'&'.join(query_params)}"

        if url_string == "?":
            url_string == ""

        return url_string

    @classmethod
    def get_filter_query(cls, base_query, filter_):
        """
        filtering works with resulttime or result only
        """

        def get_updated_query(filter_expression, field, value):
            if filter_expression == "eq":
                query = base_query.filter(field == value)

            if filter_expression == "ne":
                query = base_query.filter(field != value)

            if filter_expression == "gt":
                query = base_query.filter(field > value)

            if filter_expression == "ge":
                query = base_query.filter(field >= value)

            if filter_expression == "lt":
                query = base_query.filter(field < value)

            if filter_expression == "le":
                query = base_query.filter(field <= value)

            return query

        splits = filter_.split()
        filter_field = splits[0].lower()
        filter_expression = splits[1]
        filter_value = splits[2]

        string_operators = ["eq", "ne"]

        if filter_field == "result":
            try:
                value = float(filter_value)
                query = get_updated_query(
                    filter_expression, cast(Observations.result, Float), value
                )
            except Exception as e:
                logging.warning(e)
                value = filter_value
                if filter_expression in string_operators:
                    print("eq or ne")
                    query = get_updated_query(
                        filter_expression, Observations.result, value
                    )
                else:
                    raise Exception(" invalid filter operation ")

        elif filter_field == "resulttime":
            try:
                dt_obj = datetime.strptime(filter_value, "%d-%m-%YT%H:%M:%SZ")
                query = get_updated_query(
                    filter_expression, Observations.resulttime, dt_obj
                )
            except Exception as e:
                logging.warning(e)
                raise Exception(" value to filter is in dataformat error ")
        else:
            raise Exception(" unsupported filter field")
        return query

    @classmethod
    def get_expanded_query(cls, base_query, top, skip, expand_code, orderby, filter_):
        """
        applies join query based on expand code.
        applies limit() and offset() with top and skip paremeters
        """
        query = None

        logging.debug("func called")

        if filter_:
            base_query = Observations.get_filter_query(base_query, filter_)

        if expand_code >= 0:
            base_query = base_query.add_columns(
                Observations.id,
                Observations.result,
                Observations.resulttime,
                Observations.phenomenontime_begin,
                Observations.phenomenontime_end,
                Observations.featureofinterest_id,
                Observations.datastream_id,
            )

            if expand_code == 1 or expand_code == 3:
                base_query = base_query.join(
                    Datastreams, Observations.datastream_id == Datastreams.id
                ).add_columns(
                    Datastreams.unitofmeasurement.label("ds_unitofmeasurement"),
                    Datastreams.name.label("ds_name"),
                    Datastreams.description.label("ds_description"),
                    Datastreams.thing_id.label("ds_thing_id"),
                    Datastreams.sensor_id.label("ds_sensor_id"),
                )
            if expand_code == 2 or expand_code == 3:
                base_query = base_query.outerjoin(
                    FeaturesofInterest,
                    Observations.featureofinterest_id == FeaturesofInterest.id,
                ).add_columns(
                    FeaturesofInterest.name.label("foi_name"),
                    FeaturesofInterest.description.label("foi_description"),
                    FeaturesofInterest.feature.label("foi_feature"),
                    FeaturesofInterest.encodingtype.label("foi_encodingtype"),
                )

            # query = (
            #     base_query.order_by(Observations.resulttime.asc())
            #     .limit(top)
            #     .offset(skip)
            # )
            if orderby:
                orderbystrings = orderby.lower().split()
                if orderbystrings[0] == "result":
                    if orderbystrings[1] == "asc":
                        base_query = base_query.order_by(
                            cast(Observations.result, Float).asc()
                        )
                    else:
                        base_query = base_query.order_by(
                            cast(Observations.result, Float).desc()
                        )

                elif orderbystrings[0] == "resulttime":
                    if orderbystrings[1] == "asc":
                        base_query = base_query.order_by(Observations.resulttime.asc())
                    else:
                        base_query = base_query.order_by(Observations.resulttime.desc())

        logging.debug(str(base_query))

        return base_query.limit(top).offset(skip)

    @classmethod
    def filter_by_id(cls, id, expand_code, selects, orderby, filter_, resultformat):
        """
        applies query to filter Observations by Observation id
        """
        logging.debug(
            f"id={id}, expand_code={expand_code}, selects={selects}, orderby={orderby}, filter_={filter_}, resultformat={resultformat}"
        )
        if expand_code != -1:
            logging.debug("querying obs")
            result = Observations.get_expanded_query(
                Observations.query.filter(Observations.id == id),
                1,
                0,
                expand_code,
                orderby,
                filter_,
            ).first()

            logging.debug(str(result))
            if result is None:
                result = {"message": "No Observations with given Id found"}
            else:
                result = Observations.expand_to_selected_json(
                    result, expand_code, selects
                )
        else:
            result = {"message": "unrecognized expand options"}

        logging.debug(str(result))
        return result

    @classmethod
    def filter_by_datastream_id(
        cls, id, top, skip, expand_code, selects, orderby, filter_, resultformat
    ):
        """
        applies query to filter Observations by datastream id
        """
        count = Observations.query.filter(Observations.datastream_id == id).count()
        if count == 0:
            obs_list = {"@iot.count": count}  ## TODO update count with filter
        elif resultformat:
            obs_list = {
                "@iot.count": count,
                "@iot.nextLink": f"{current_app.config['HOSTED_URL']}/Datastreams({id})/Observations{Observations.get_nextlink_queryparams(top, skip, 0, resultformat)}",  # TODO
                "components": [
                    "@iot.id",
                    "phenonmenontime_begin",
                    "result",
                    "resulttime",
                ],
                "dataArray": list(
                    map(
                        lambda x: Observations.to_dataarray(x),
                        Observations.get_expanded_query(
                            Observations.query.filter(Observations.datastream_id == id),
                            top,
                            skip,
                            0,
                            orderby,
                            filter_,
                        ).all(),
                    )
                ),
            }
        elif expand_code != -1:
            obs_list = {
                "@iot.count": count,
                "@iot.nextLink": f"{current_app.config['HOSTED_URL']}/Datastreams({id})/Observations{Observations.get_nextlink_queryparams(top, skip, expand_code, None)}",
                "value": list(
                    map(
                        lambda x: Observations.expand_to_selected_json(
                            x, expand_code, selects
                        ),
                        Observations.get_expanded_query(
                            Observations.query.filter(Observations.datastream_id == id),
                            top,
                            skip,
                            expand_code,
                            orderby,
                            filter_,
                        ).all(),
                    )
                ),
            }
        else:
            obs_list = {"error": "unrecognized expand options"}
        return obs_list

    @classmethod
    def return_page_with_expand(
        cls, top, skip, expand_code, selects, orderby, filter_, resultformat
    ):
        """
        applies query to join Observations table with Datastreams table of FeatureOfInterest table or both
        based on expand code
        """
        count = Observations.query.count()
        if count == 0:
            obs_list = {"@iot.count": count}
        elif resultformat:
            obs_list = {
                "@iot.count": count,
                "@iot.nextLink": f"{current_app.config['HOSTED_URL']}/Observations{Observations.get_nextlink_queryparams(top, skip, 0, resultformat)}",  # TODO
                "components": [
                    "@iot.id",
                    "phenonmenontime_begin",
                    "result",
                    "resulttime",
                ],
                "dataArray": list(
                    map(
                        lambda x: Observations.to_dataarray(x),
                        Observations.get_expanded_query(
                            Observations.query, top, skip, 0, orderby, filter_
                        ).all(),
                    )
                ),
            }
        elif expand_code != -1:
            obs_list = {
                "@iot.count": count,
                "@iot.nextLink": f"{current_app.config['HOSTED_URL']}/Observations{Observations.get_nextlink_queryparams(top, skip, expand_code, None)}",
                "value": list(
                    map(
                        lambda x: Observations.expand_to_selected_json(
                            x, expand_code, selects
                        ),
                        Observations.get_expanded_query(
                            Observations.query, top, skip, expand_code, orderby, filter_
                        ).all(),
                    )
                ),
            }
        else:
            obs_list = {"error": "unrecognized expand options"}

        return obs_list

    @classmethod
    def find_observation_by_observation_id(cls, id):
        """
        applies query to filter Observations by Observation id
        """

        result = Observations.query.filter(Observations.id == id).first()

        return result
