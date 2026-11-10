from ollama import chat
import predictor


user_message = {
    "role": "user",
    "content": "Make a prediction using the five input features: hour=14, month=5, day_of_week=2, lag_1h=150.0, lag_24h=145.0"
}

response = chat(
    model="qwen3:4b",
    messages=[user_message],
    tools=[predictor.predict_power]
)

print(response.message.tool_calls)

first_call = response.message.tool_calls[0]
print(first_call.function)

prediction_args = first_call.function.arguments
# print(prediction_args)
# print(type(prediction_args["hour"]))

# prediction_args["hour"] = int(prediction_args["hour"])
# prediction_args["month"] = int(prediction_args["month"])
# prediction_args["day_of_week"] = int(prediction_args["day_of_week"])
# prediction_args["lag_1h"] = float(prediction_args["lag_1h"])
# prediction_args["lag_24h"] = float(prediction_args["lag_24h"])

#for key, value in prediction_args.items():
    #print(key, value, type(value))

prediction = predictor.predict_power(**prediction_args)
print(prediction)

tool_result = {
    "role": "tool",
    "tool_name": "predict_power",
    "content": f"The predicted power consumption is {prediction} kW"
}

result_response = chat(
    model="qwen3:4b",
    messages=[
    user_message,
    response.message,
    tool_result
])

print(result_response.message.content)