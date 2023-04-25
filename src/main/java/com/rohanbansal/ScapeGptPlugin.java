package com.rohanbansal;

import com.google.gson.Gson;
import com.google.inject.Provides;

import java.awt.image.BufferedImage;
import java.util.concurrent.TimeUnit;
import javax.inject.Inject;

import lombok.extern.slf4j.Slf4j;
import net.runelite.client.account.AccountSession;
import net.runelite.client.account.SessionManager;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.ui.ClientToolbar;
import net.runelite.client.ui.NavigationButton;
import net.runelite.client.util.ImageUtil;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;

@Slf4j
@PluginDescriptor(name = "ScapeGPT", loadWhenOutdated = true)
public class ScapeGptPlugin extends Plugin {
    private static final String HOST = "44.211.86.102";  // Server IP address that handles requests
    private static final String ENDPOINT = "api/v1/query";
    private static final String LOGO = "scapegpt-icon.png";
    private static final int HTTP_TIMEOUT_SECONDS = 45;  // Both connection and waiting for response
    @Inject
    private ClientToolbar clientToolbar;
    @Inject
    private ScapeGptConfig config;
    @Inject
    private SessionManager sessionManager;
    @Inject
    private Gson gson;
    @Inject
    private OkHttpClient httpClient;
    private ScapeGptClient scapeGptClient;
    private ScapeGptPanel panel;
    private NavigationButton navButton;
    private HttpUrl apiUrl;

    @Override
    protected void startUp() {
        apiUrl = new HttpUrl.Builder().scheme("http").host(HOST).addPathSegments(ENDPOINT).build();
        scapeGptClient = new ScapeGptClient(httpClient.newBuilder().connectTimeout(HTTP_TIMEOUT_SECONDS, TimeUnit.SECONDS).readTimeout(HTTP_TIMEOUT_SECONDS, TimeUnit.SECONDS).build(), apiUrl, gson);

        AccountSession accountSession = sessionManager.getAccountSession();
        if (accountSession != null) {
            scapeGptClient.setUuid(accountSession.getUuid());
        } else {
            scapeGptClient.setUuid(null);
        }

        panel = injector.getInstance(ScapeGptPanel.class);
        panel.init(scapeGptClient);

        final BufferedImage icon = ImageUtil.loadImageResource(getClass(), LOGO);

        navButton = NavigationButton.builder().tooltip("ScapeGPT").icon(icon).priority(13).panel(panel).build();

        clientToolbar.addNavigation(navButton);
    }

    @Override
    protected void shutDown() {
        clientToolbar.removeNavigation(navButton);
    }

    @Provides
    ScapeGptConfig provideConfig(ConfigManager configManager) {
        return configManager.getConfig(ScapeGptConfig.class);
    }
}
