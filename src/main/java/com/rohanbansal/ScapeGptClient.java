package com.rohanbansal;

import com.google.gson.Gson;
import com.google.gson.JsonObject;

import java.io.IOException;

import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static net.runelite.http.api.RuneLiteAPI.JSON;

public class ScapeGptClient {
    private final OkHttpClient client;
    private final HttpUrl apiUrl;
    private final Gson gson;

    public ScapeGptClient(OkHttpClient client, HttpUrl apiUrl, Gson gson) {
        this.client = client;
        this.apiUrl = apiUrl;
        this.gson = gson;
    }

    public String getResponse(String prompt) {
        Request.Builder builder = new Request.Builder();

        JsonObject jsonObject = new JsonObject();
        jsonObject.addProperty("prompt", prompt);

        Request request = builder
                .post(RequestBody.create(JSON, gson.toJson(jsonObject)))
                .url(apiUrl)
                .build();

        try {
            Response response = client.newCall(request).execute();
            if (!response.isSuccessful()) throw new Exception("Unexpected code " + response);

            String jsonData = response.body().string();
            JsonObject json = gson.newBuilder().create().fromJson(jsonData, JsonObject.class);
            return json.get("res").getAsString().trim();
        } catch (IOException e) {
            String errorMessage = e.getMessage();
            System.err.println("Error making request: " + errorMessage);
            return "An unknown error occurred. Please try again in 1 minute.";
        } catch (Exception e) {
            String errorMessage = e.getMessage();
            System.err.println("Unexpected error: " + errorMessage);
            if (errorMessage.contains("code=429")) {
                return "Too many requests! There is a limit of 3 queries per minute, and 20 queries per day.";
            } else {
                return "An unknown error occurred. Please try again in 1 minute.";
            }
        }
    }
}
