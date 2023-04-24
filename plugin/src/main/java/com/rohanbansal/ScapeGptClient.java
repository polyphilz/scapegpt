package com.rohanbansal;

import com.google.gson.Gson;
import com.google.gson.JsonObject;

import java.io.IOException;
import java.util.UUID;

import lombok.Setter;
import net.runelite.http.api.RuneLiteAPI;
import okhttp3.Call;
import okhttp3.Callback;
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

    @Setter
    private UUID uuid;

    public ScapeGptClient(OkHttpClient client, HttpUrl apiUrl, Gson gson) {
        this.client = client;
        this.apiUrl = apiUrl;
        this.gson = gson;
    }

    public String getResponse(String prompt) {
        Request.Builder builder = new Request.Builder();
        if (uuid != null) {
            builder.header(RuneLiteAPI.RUNELITE_AUTH, uuid.toString());
        }

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
            Gson somegson = new Gson();
            JsonObject ff = somegson.fromJson(jsonData, JsonObject.class);
            String resValue = ff.get("res").getAsString().trim();
            return resValue;
        } catch (IOException e) {
            String errorMessage = e.getMessage();
            System.err.println("Error making request: " + errorMessage);
            return "An unknown error occurred. Please try again in 1 minute.";
        } catch (Exception e) {
            String errorMessage = e.getMessage();
            System.err.println("Unexpected error: " + errorMessage);
            if (errorMessage.contains("code=429")) {
                return "Too many requests! There is a limit of 3 queries per minute, and 30 queries per day.";
            } else {
                return "An unknown error occurred. Please try again in 1 minute.";
            }
        }
    }
}
