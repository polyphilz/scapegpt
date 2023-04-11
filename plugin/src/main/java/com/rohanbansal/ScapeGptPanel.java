package com.rohanbansal;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.Insets;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.io.IOException;
import javax.inject.Inject;
import javax.swing.BorderFactory;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.border.EmptyBorder;
import javax.swing.text.BadLocationException;
import javax.swing.text.Document;
import javax.swing.text.AbstractDocument;
import javax.swing.text.AttributeSet;
import javax.swing.text.DocumentFilter;
import lombok.extern.slf4j.Slf4j;
import net.runelite.client.ui.ColorScheme;
import net.runelite.client.ui.PluginPanel;
import net.runelite.http.api.RuneLiteAPI;
import static net.runelite.http.api.RuneLiteAPI.JSON;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import net.runelite.client.account.AccountSession;
import net.runelite.client.account.SessionManager;

@Slf4j
class ScapeGptPanel extends PluginPanel {
    @Inject
    private SessionManager sessionManager;

    private final JLabel promptInputFieldLabel = new JLabel("<html>Ask ScapeGPT anything! Enter text and press Shift+Enter to submit:<br/><br/></html>");
    private final JTextArea promptInputField = new JTextArea();
    private final JTextArea responseArea = new JTextArea();

    private String prompt = "";

    void init() {
        setBackground(ColorScheme.DARK_GRAY_COLOR);

        // Custom settings for the prompt input text area
        promptInputField.setTabSize(2);
        promptInputField.setLineWrap(true);
        promptInputField.setWrapStyleWord(true);
        promptInputField.setMargin(new Insets(10, 10, 10, 10));
        final JScrollPane promptInputScrollPane = new JScrollPane(promptInputField);
        promptInputScrollPane.setPreferredSize(new Dimension(promptInputField.getPreferredSize().width, 100));
        promptInputScrollPane.setBorder(BorderFactory.createLineBorder(ColorScheme.BRAND_ORANGE));

        // Custom settings for the response text area
        responseArea.setEditable(false);
        responseArea.setLineWrap(true);
        responseArea.setWrapStyleWord(true);
        responseArea.setMargin(new Insets(10, 10, 10, 10));
        final JScrollPane responseScrollPane = new JScrollPane(responseArea);
        responseScrollPane.setPreferredSize(new Dimension(responseArea.getPreferredSize().width, 400));

        JPanel promptContainer = new JPanel();
        promptContainer.setLayout(new BorderLayout());
        promptContainer.setBackground(ColorScheme.DARKER_GRAY_COLOR);
        promptContainer.setOpaque(false);

        JPanel responseContainer = new JPanel();
        responseContainer.setLayout(new BoxLayout(responseContainer, BoxLayout.Y_AXIS));
        responseContainer.setBackground(ColorScheme.DARKER_GRAY_COLOR);
        responseContainer.add(Box.createVerticalStrut(10)); // add some vertical space
        responseContainer.setOpaque(false);

        // Add all event listeners
        addPromptInputFieldEventListeners();

        promptContainer.add(promptInputFieldLabel, BorderLayout.NORTH);
        promptContainer.add(promptInputScrollPane, BorderLayout.CENTER);
        promptContainer.setBorder(new EmptyBorder(10, 10, 10, 10));

        responseContainer.add(responseScrollPane, BorderLayout.NORTH);
        responseContainer.setBorder(new EmptyBorder(10, 10, 10, 10));

        add(promptContainer, BorderLayout.NORTH);
        add(responseContainer, BorderLayout.SOUTH);
    }

    private String getTextFromDocument(Document document) {
        try {
            return document.getText(0, document.getLength());
        } catch (BadLocationException ex) {
            // handle the exception
            return null;
        }
    }

    private void addPromptInputFieldEventListeners() {
        addPromptInputFieldKeyEventListener();
        addPromptInputFieldDocumentListener();
        addPromptInputFieldDocumentFilterListener();
    }

    private void addPromptInputFieldKeyEventListener() {
        promptInputField.addKeyListener(new KeyAdapter() {
            @Override
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_ENTER && e.isShiftDown()) {
                    promptScapeGptBackend();
                }
            }
        });
    }

    private void addPromptInputFieldDocumentListener() {
        promptInputField.getDocument().addDocumentListener(new DocumentListener() {
            @Override
            public void insertUpdate(DocumentEvent e) {
                prompt = getTextFromDocument(e.getDocument());
            }

            @Override
            public void removeUpdate(DocumentEvent e) {
                prompt = getTextFromDocument(e.getDocument());
            }

            @Override
            public void changedUpdate(DocumentEvent e) {}  // Unused
        });
    }

    private void addPromptInputFieldDocumentFilterListener() {
        ((AbstractDocument) promptInputField.getDocument()).setDocumentFilter(new DocumentFilter() {
            private final int maxLength = 200;

            @Override
            public void insertString(FilterBypass fb, int offset, String text, AttributeSet attrs) throws BadLocationException {
                if ((fb.getDocument().getLength() + text.length()) <= maxLength) {
                    super.insertString(fb, offset, text, attrs);
                }
            }

            @Override
            public void remove(FilterBypass fb, int offset, int length) throws BadLocationException {
                super.remove(fb, offset, length);
            }

            @Override
            public void replace(FilterBypass fb, int offset, int length, String text, AttributeSet attrs) throws BadLocationException {
                if ((fb.getDocument().getLength() - length + text.length()) <= maxLength) {
                    super.replace(fb, offset, length, text, attrs);
                }
            }
        });
    }

    private void promptScapeGptBackend() {
        AccountSession accountSession = sessionManager.getAccountSession();
//        if (accountSession != null)
//        {
//            System.out.println(accountSession.getUuid());
//        }
        System.out.println(prompt);
//        System.out.println(RuneLiteAPI.RUNELITE_AUTH);

        OkHttpClient client = new OkHttpClient();
        HttpUrl.Builder apiBase = new HttpUrl.Builder().scheme("http").host("127.0.0.1").port(4747);
        System.out.println(apiBase);
        Gson gson = new Gson();

        final HttpUrl url = apiBase.build();
        System.out.println(url);
        Request.Builder builder = new Request.Builder();

        JsonObject jsonObject = new JsonObject();
        jsonObject.addProperty("prompt", prompt);

        Request request = builder
                .post(RequestBody.create(JSON, gson.toJson(jsonObject)))
                .url(url)
                .build();

        try {
            Response response = client.newCall(request).execute();
            if (!response.isSuccessful()) throw new Exception("Unexpected code " + response);

            String jsonData = response.body().string();
            Gson somegson = new Gson();
            JsonObject ff = somegson.fromJson(jsonData, JsonObject.class);
            String resValue = ff.get("res").getAsString();
            System.out.println(resValue);
            responseArea.setText(resValue);
        } catch (IOException e) {
            System.err.println("Error making request: " + e.getMessage());
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
        }
    }
}